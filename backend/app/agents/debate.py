"""Debater agents, evaluator chain, and the round-by-round orchestrator.

Fixes vs. the PRD reference:
- Uses `create_tool_calling_agent` + `AgentExecutor(agent=agent, tools=tools)`
  (the modern Runnable-based API), not the nonexistent
  `AgentExecutor.from_agent_and_tools(...)`.
- The evaluator is a dedicated structured-output chain, not a tool the
  debater calls on itself, and it never trusts a bare `float(response.content)`
  — it uses `.with_structured_output(RoundScore)` where supported, with a
  regex-based fallback parser so a single malformed response never crashes
  the debate.
- `run_debate` streams round-by-round via an `on_round_complete` callback
  instead of only returning after every round has finished.
"""
from __future__ import annotations

import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agents.schemas import RoundScore
from app.agents.tools import DEBATE_TOOLS

logger = logging.getLogger(__name__)

DEBATER_SYSTEM_PROMPT = """You are an expert debater arguing the {position} position on the topic: "{topic}".

Rules:
- Write ONE persuasive argument for this round (150-250 words).
- Use the search_evidence tool at least once to ground your argument in real facts/citations when useful.
- Directly address the opposing side's most recent argument if one is provided, rebutting its weakest point.
- Be concise, logical, and avoid repeating earlier rounds verbatim.
- Do not concede the debate or argue both sides.
"""

EVALUATOR_SYSTEM_PROMPT = """You are an impartial debate judge. Score the following argument on these four \
dimensions and return ONLY the structured fields requested:
- logical_strength (0-3): validity and rigor of the reasoning
- evidence_quality (0-3): quality/specificity of evidence or citations used
- clarity (0-2): how clearly and persuasively it is written
- counterargument_handling (0-2): how well it engages with/rebuts the opposing side

Topic: {topic}
Position being judged: {position}
Opposing argument (if any): {opposing_argument}

Argument to score:
{argument}
"""

_SCORE_FIELD_PATTERN = re.compile(
    r"logical_strength\D{0,10}?(-?\d+(?:\.\d+)?).*?"
    r"evidence_quality\D{0,10}?(-?\d+(?:\.\d+)?).*?"
    r"clarity\D{0,10}?(-?\d+(?:\.\d+)?).*?"
    r"counterargument_handling\D{0,10}?(-?\d+(?:\.\d+)?)",
    re.IGNORECASE | re.DOTALL,
)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _fallback_parse_score(text: str) -> RoundScore:
    """Regex fallback for when structured output isn't reliable (e.g. small local models)."""
    match = _SCORE_FIELD_PATTERN.search(text)
    if match:
        logical, evidence, clarity, counter = (float(g) for g in match.groups())
        return RoundScore(
            logical_strength=_clamp(logical, 0, 3),
            evidence_quality=_clamp(evidence, 0, 3),
            clarity=_clamp(clarity, 0, 2),
            counterargument_handling=_clamp(counter, 0, 2),
            feedback=text.strip()[:500] or "No feedback text parsed.",
        )

    # Last-resort fallback: no parseable numbers at all. Give a conservative
    # mid-range score rather than crashing the round.
    logger.warning("Evaluator response had no parseable score fields; using conservative default scores.")
    return RoundScore(
        logical_strength=1.5,
        evidence_quality=1.5,
        clarity=1.0,
        counterargument_handling=1.0,
        feedback=f"Could not reliably parse a structured score from the model response. Raw: {text.strip()[:300]}",
    )


def create_debater_agent(llm: BaseChatModel, tools: list, position: str, topic: str) -> AgentExecutor:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", DEBATER_SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    ).partial(position=position, topic=topic)
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, max_iterations=4, handle_parsing_errors=True)


class EvaluatorChain:
    """Structured-output scoring chain with a robust fallback parser."""

    def __init__(self, llm: BaseChatModel):
        self._llm = llm
        try:
            self._structured_llm = llm.with_structured_output(RoundScore)
            self._supports_structured = True
        except (NotImplementedError, AttributeError):
            self._structured_llm = None
            self._supports_structured = False

    async def ascore(self, topic: str, position: str, argument: str, opposing_argument: str | None) -> RoundScore:
        prompt = EVALUATOR_SYSTEM_PROMPT.format(
            topic=topic,
            position=position,
            opposing_argument=opposing_argument or "(none yet)",
            argument=argument,
        )
        if self._supports_structured:
            try:
                result = await self._structured_llm.ainvoke(prompt)
                if isinstance(result, RoundScore):
                    return result
                if isinstance(result, dict):
                    return RoundScore(**result)
            except Exception as exc:
                logger.info("Structured evaluator output failed (%s); falling back to regex parsing.", exc)

        raw = await self._llm.ainvoke(
            prompt
            + "\n\nRespond with exactly these lines:\n"
            "logical_strength: <0-3>\nevidence_quality: <0-3>\nclarity: <0-2>\n"
            "counterargument_handling: <0-2>\nfeedback: <one sentence>"
        )
        text = raw.content if hasattr(raw, "content") else str(raw)
        return _fallback_parse_score(text)


def create_evaluator_chain(llm: BaseChatModel) -> EvaluatorChain:
    return EvaluatorChain(llm)


@dataclass
class RoundResult:
    round_number: int
    pro_argument: str
    pro_score: RoundScore
    con_argument: str
    con_score: RoundScore
    pro_total: float = field(init=False)
    con_total: float = field(init=False)

    def __post_init__(self) -> None:
        self.pro_total = self.pro_score.total
        self.con_total = self.con_score.total


OnRoundComplete = Callable[[RoundResult], Awaitable[None]]


class DebateOrchestrator:
    def __init__(self, llm: BaseChatModel, tools: list | None = None):
        tools = tools if tools is not None else DEBATE_TOOLS
        self._llm = llm
        self._tools = tools
        self.evaluator = create_evaluator_chain(llm)

    async def run_debate(self, topic: str, num_rounds: int, on_round_complete: OnRoundComplete) -> dict[str, Any]:
        self.pro_agent = create_debater_agent(self._llm, self._tools, "Pro (in favor)", topic)
        self.con_agent = create_debater_agent(self._llm, self._tools, "Con (against)", topic)
        pro_total, con_total = 0.0, 0.0
        last_pro_arg: str | None = None
        last_con_arg: str | None = None

        for round_number in range(1, num_rounds + 1):
            pro_input = (
                f"Round {round_number}. Present your argument for the Pro side."
                + (f" The Con side's previous argument was: {last_con_arg}" if last_con_arg else "")
            )
            pro_result = await self.pro_agent.ainvoke({"input": pro_input})
            pro_argument = pro_result["output"]

            con_input = (
                f"Round {round_number}. Present your argument for the Con side, "
                f"rebutting the Pro side's argument: {pro_argument}"
            )
            con_result = await self.con_agent.ainvoke({"input": con_input})
            con_argument = con_result["output"]

            pro_score = await self.evaluator.ascore(topic, "Pro", pro_argument, last_con_arg)
            con_score = await self.evaluator.ascore(topic, "Con", con_argument, pro_argument)

            pro_total += pro_score.total
            con_total += con_score.total
            last_pro_arg, last_con_arg = pro_argument, con_argument

            result = RoundResult(
                round_number=round_number,
                pro_argument=pro_argument,
                pro_score=pro_score,
                con_argument=con_argument,
                con_score=con_score,
            )
            await on_round_complete(result)

        winner = "pro" if pro_total > con_total else "con" if con_total > pro_total else "tie"
        return {"pro_score": pro_total, "con_score": con_total, "winner": winner}

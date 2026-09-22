"""A deterministic fake chat model used in CI where no Ollama/Anthropic is available."""
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class FakeDebateLLM(BaseChatModel):
    """Cycles through canned debate-argument and evaluator-score responses."""

    call_count: int = 0

    @property
    def _llm_type(self) -> str:
        return "fake-debate-llm"

    def _generate(self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs: Any) -> ChatResult:
        text = messages[-1].content if messages else ""
        self.call_count += 1

        if "logical_strength" in text.lower() and "counterargument_handling" in text.lower():
            content = (
                "logical_strength: 2.5\n"
                "evidence_quality: 2.0\n"
                "clarity: 1.5\n"
                "counterargument_handling: 1.5\n"
                "feedback: Reasonably persuasive with adequate support."
            )
        else:
            content = "This is a fake debate argument used for deterministic CI testing. (call #%d)" % self.call_count

        message = AIMessage(content=content)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    def bind_tools(self, tools, **kwargs):
        return self

    def with_structured_output(self, schema, **kwargs):
        raise NotImplementedError("FakeDebateLLM always exercises the regex fallback parser")

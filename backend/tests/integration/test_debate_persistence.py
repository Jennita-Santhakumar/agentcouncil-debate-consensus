import uuid

import pytest

from app.agents.debate import DebateOrchestrator
from app.core.models import Debate, DebateRound
from tests.integration.fake_llm import FakeDebateLLM


@pytest.mark.asyncio
async def test_full_debate_run_persists_rows(db_session):
    debate = Debate(id=uuid.uuid4(), topic="Should remote work be the default?", num_rounds=2, status="running")
    db_session.add(debate)
    await db_session.commit()

    llm = FakeDebateLLM()
    orchestrator = DebateOrchestrator(llm, tools=[])

    persisted_rounds = []

    async def on_round_complete(result):
        row = DebateRound(
            debate_id=debate.id,
            round_number=result.round_number,
            pro_argument=result.pro_argument,
            pro_score_breakdown={"total": result.pro_total},
            con_argument=result.con_argument,
            con_score_breakdown={"total": result.con_total},
        )
        db_session.add(row)
        await db_session.commit()
        persisted_rounds.append(row)

    outcome = await orchestrator.run_debate("Should remote work be the default?", 2, on_round_complete)

    assert len(persisted_rounds) == 2
    assert outcome["winner"] in {"pro", "con", "tie"}
    assert persisted_rounds[0].round_number == 1
    assert persisted_rounds[1].round_number == 2
    for row in persisted_rounds:
        assert row.pro_argument
        assert row.con_argument

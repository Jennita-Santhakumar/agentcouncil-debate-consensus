import asyncio

import pytest

from app.agents.debate import DebateOrchestrator
from app.api.ws_manager import ConnectionManager
from tests.integration.fake_llm import FakeDebateLLM


class FakeWebSocket:
    def __init__(self):
        self.sent: list[dict] = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_json(self, message: dict):
        self.sent.append(message)


@pytest.mark.asyncio
async def test_round_messages_arrive_in_order_before_debate_complete():
    manager = ConnectionManager()
    ws = FakeWebSocket()
    await manager.connect("debate-1", ws)

    llm = FakeDebateLLM()
    orchestrator = DebateOrchestrator(llm, tools=[])

    async def on_round_complete(result):
        await manager.broadcast("debate-1", {"type": "round_complete", "round_number": result.round_number})

    outcome = await orchestrator.run_debate("Is remote work better?", 3, on_round_complete)
    await manager.broadcast("debate-1", {"type": "debate_complete", "winner": outcome["winner"]})

    types = [m["type"] for m in ws.sent]
    assert types == ["round_complete", "round_complete", "round_complete", "debate_complete"]
    round_numbers = [m["round_number"] for m in ws.sent[:-1]]
    assert round_numbers == [1, 2, 3]

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.debate import DebateOrchestrator, RoundResult
from app.api.schemas import DebateCreateRequest, DebateCreateResponse, DebateOut, DebateSummaryOut
from app.api.ws_manager import manager
from app.core.db import AsyncSessionLocal, get_db
from app.core.models import Debate, DebateRound
from app.llm.factory import get_llm

logger = logging.getLogger(__name__)
router = APIRouter()


def _score_dict(score) -> dict:
    return {
        "logical_strength": score.logical_strength,
        "evidence_quality": score.evidence_quality,
        "clarity": score.clarity,
        "counterargument_handling": score.counterargument_handling,
        "feedback": score.feedback,
        "total": score.total,
    }


async def _run_and_persist_debate(debate_id: uuid.UUID, topic: str, num_rounds: int) -> None:
    """Runs the debate in the background, persisting + broadcasting each round as it completes."""

    async def on_round_complete(result: RoundResult) -> None:
        async with AsyncSessionLocal() as session:
            round_row = DebateRound(
                debate_id=debate_id,
                round_number=result.round_number,
                pro_argument=result.pro_argument,
                pro_score_breakdown=_score_dict(result.pro_score),
                con_argument=result.con_argument,
                con_score_breakdown=_score_dict(result.con_score),
            )
            session.add(round_row)

            debate_row = await session.get(Debate, debate_id)
            debate_row.pro_score = (debate_row.pro_score or 0.0) + result.pro_total
            debate_row.con_score = (debate_row.con_score or 0.0) + result.con_total
            await session.commit()

            payload = {
                "type": "round_complete",
                "debate_id": str(debate_id),
                "round_number": result.round_number,
                "pro_argument": result.pro_argument,
                "pro_score_breakdown": _score_dict(result.pro_score),
                "con_argument": result.con_argument,
                "con_score_breakdown": _score_dict(result.con_score),
                "running_pro_score": debate_row.pro_score,
                "running_con_score": debate_row.con_score,
            }
        await manager.broadcast(str(debate_id), payload)

    try:
        llm = get_llm()
        orchestrator = DebateOrchestrator(llm)
        outcome = await orchestrator.run_debate(topic, num_rounds, on_round_complete)

        async with AsyncSessionLocal() as session:
            debate_row = await session.get(Debate, debate_id)
            debate_row.status = "completed"
            debate_row.winner = outcome["winner"]
            debate_row.completed_at = datetime.now(UTC)
            await session.commit()

        await manager.broadcast(
            str(debate_id),
            {
                "type": "debate_complete",
                "debate_id": str(debate_id),
                "winner": outcome["winner"],
                "pro_score": outcome["pro_score"],
                "con_score": outcome["con_score"],
            },
        )
    except Exception as exc:
        logger.exception("Debate %s failed", debate_id)
        async with AsyncSessionLocal() as session:
            debate_row = await session.get(Debate, debate_id)
            if debate_row is not None:
                debate_row.status = "failed"
                debate_row.completed_at = datetime.now(UTC)
                await session.commit()
        await manager.broadcast(
            str(debate_id), {"type": "debate_failed", "debate_id": str(debate_id), "error": str(exc)}
        )


@router.post("/debates", response_model=DebateCreateResponse, status_code=201)
async def create_debate(
    body: DebateCreateRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
) -> DebateCreateResponse:
    debate = Debate(topic=body.topic, num_rounds=body.num_rounds, status="running")
    db.add(debate)
    await db.commit()
    await db.refresh(debate)

    background_tasks.add_task(_run_and_persist_debate, debate.id, body.topic, body.num_rounds)
    return DebateCreateResponse(debate_id=debate.id)


@router.get("/debates", response_model=list[DebateSummaryOut])
async def list_debates(db: AsyncSession = Depends(get_db)) -> list[Debate]:
    result = await db.execute(select(Debate).order_by(Debate.created_at.desc()))
    return list(result.scalars().all())


@router.get("/debates/{debate_id}", response_model=DebateOut)
async def get_debate(debate_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Debate:
    from sqlalchemy.orm import selectinload

    result = await db.execute(select(Debate).options(selectinload(Debate.rounds)).where(Debate.id == debate_id))
    debate = result.scalar_one_or_none()
    if debate is None:
        raise HTTPException(status_code=404, detail="Debate not found")
    return debate


ws_router = APIRouter()


@ws_router.websocket("/ws/debate/{debate_id}")
async def debate_websocket(websocket: WebSocket, debate_id: str) -> None:
    await manager.connect(debate_id, websocket)
    try:
        while True:
            # Client doesn't need to send anything; keep the connection open
            # until it disconnects. Receiving lets us detect that promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(debate_id, websocket)

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DebateCreateRequest(BaseModel):
    topic: str = Field(min_length=4, max_length=500)
    num_rounds: int = Field(default=3, ge=1, le=10)


class DebateCreateResponse(BaseModel):
    debate_id: uuid.UUID


class ScoreBreakdown(BaseModel):
    logical_strength: float
    evidence_quality: float
    clarity: float
    counterargument_handling: float
    feedback: str
    total: float


class RoundOut(BaseModel):
    round_number: int
    pro_argument: str
    pro_score_breakdown: dict
    con_argument: str
    con_score_breakdown: dict

    model_config = {"from_attributes": True}


class DebateOut(BaseModel):
    id: uuid.UUID
    topic: str
    num_rounds: int
    status: str
    pro_score: float
    con_score: float
    winner: str | None
    created_at: datetime
    completed_at: datetime | None
    rounds: list[RoundOut] = []

    model_config = {"from_attributes": True}


class DebateSummaryOut(BaseModel):
    id: uuid.UUID
    topic: str
    num_rounds: int
    status: str
    pro_score: float
    con_score: float
    winner: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

import pytest

from app.agents.debate import RoundResult
from app.agents.schemas import RoundScore


def test_round_result_totals_computed_from_subscores():
    pro_score = RoundScore(logical_strength=3, evidence_quality=2, clarity=2, counterargument_handling=1, feedback="x")
    con_score = RoundScore(logical_strength=1, evidence_quality=1, clarity=1, counterargument_handling=1, feedback="y")
    result = RoundResult(
        round_number=1, pro_argument="pro arg", pro_score=pro_score, con_argument="con arg", con_score=con_score
    )
    assert result.pro_total == 8
    assert result.con_total == 4


def test_round_score_rejects_out_of_range_via_pydantic():
    with pytest.raises(ValueError):
        RoundScore(logical_strength=5, evidence_quality=0, clarity=0, counterargument_handling=0, feedback="x")

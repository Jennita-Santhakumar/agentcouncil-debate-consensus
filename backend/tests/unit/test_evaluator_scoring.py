from app.agents.debate import _fallback_parse_score
from app.agents.schemas import RoundScore


def test_fallback_parse_score_well_formed():
    text = (
        "logical_strength: 2.5\n"
        "evidence_quality: 2.0\n"
        "clarity: 1.5\n"
        "counterargument_handling: 1.0\n"
        "feedback: Solid argument with good use of evidence."
    )
    score = _fallback_parse_score(text)
    assert score.logical_strength == 2.5
    assert score.evidence_quality == 2.0
    assert score.clarity == 1.5
    assert score.counterargument_handling == 1.0
    assert score.total == 7.0


def test_fallback_parse_score_out_of_range_values_are_clamped():
    text = (
        "logical_strength: 9\n"
        "evidence_quality: -3\n"
        "clarity: 10\n"
        "counterargument_handling: 5\n"
        "feedback: extreme values"
    )
    score = _fallback_parse_score(text)
    assert score.logical_strength == 3
    assert score.evidence_quality == 0
    assert score.clarity == 2
    assert score.counterargument_handling == 2


def test_fallback_parse_score_malformed_response_does_not_crash():
    text = "I think this argument was pretty good overall, hard to say exactly."
    score = _fallback_parse_score(text)
    assert isinstance(score, RoundScore)
    assert 0 <= score.total <= 10


def test_round_score_total_is_sum_of_subscores():
    score = RoundScore(
        logical_strength=3, evidence_quality=3, clarity=2, counterargument_handling=2, feedback="great"
    )
    assert score.total == 10

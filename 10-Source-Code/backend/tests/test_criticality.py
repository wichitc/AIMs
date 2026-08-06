import pytest

from app.modules.asset.service import _CRITICALITY_WEIGHTS, _rank_from_score


def test_weights_sum_to_one():
    assert sum(_CRITICALITY_WEIGHTS.values()) == pytest.approx(1.0)


def test_safety_is_weighted_highest():
    # Safety-weighted per API 580 — a pure-safety asset should outrank a pure-economic
    # asset even with the same raw score, since safety carries the largest weight.
    assert _CRITICALITY_WEIGHTS["safety"] > _CRITICALITY_WEIGHTS["environmental"]
    assert _CRITICALITY_WEIGHTS["safety"] > _CRITICALITY_WEIGHTS["economic"]


@pytest.mark.parametrize(
    "score,expected_level",
    [(0, "Low"), (34.9, "Low"), (35, "Medium"), (59.9, "Medium"), (60, "High"), (79.9, "High"), (80, "VeryHigh"), (100, "VeryHigh")],
)
def test_rank_from_score_boundaries(score, expected_level):
    assert _rank_from_score(score) == expected_level


def test_calculated_score_uses_documented_weights():
    safety, environmental, economic = 90, 40, 20
    calculated = (
        safety * _CRITICALITY_WEIGHTS["safety"]
        + environmental * _CRITICALITY_WEIGHTS["environmental"]
        + economic * _CRITICALITY_WEIGHTS["economic"]
    )

    assert calculated == pytest.approx(61.0)
    assert _rank_from_score(calculated) == "High"

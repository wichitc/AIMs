import pytest

from app.modules.rbi.service import (
    _COF_WEIGHT,
    _governing_cof,
    _pof_category,
    _rank_from_score,
)


@pytest.mark.parametrize(
    "safety,environmental,expected",
    [
        ("Low", "Medium", "Medium"),
        ("Critical", "Low", "Critical"),
        (None, "High", "High"),
        (None, None, "Medium"),  # no data supplied -> conservative default
    ],
)
def test_governing_cof_takes_the_worse_of_safety_and_environmental(safety, environmental, expected):
    assert _governing_cof(safety, environmental) == expected


@pytest.mark.parametrize(
    "score,expected_rank",
    [
        (0.0, "Low"),
        (2.9, "Low"),
        (3.0, "Medium"),
        (7.9, "Medium"),
        (8.0, "High"),
        (14.9, "High"),
        (15.0, "VeryHigh"),
        (100.0, "VeryHigh"),
    ],
)
def test_rank_from_score_boundaries(score, expected_rank):
    assert _rank_from_score(score) == expected_rank


@pytest.mark.parametrize(
    "pof_score,expected_category",
    [(0.0, "1"), (0.4, "1"), (3.0, "3"), (5.0, "5"), (7.0, "5")],  # 7.0 clamps to the max category
)
def test_pof_category_buckets_into_1_through_5(pof_score, expected_category):
    assert _pof_category(pof_score) == expected_category


def test_risk_score_formula_is_pof_times_cof_weight():
    pof_score = 4.0
    governing_cof = _governing_cof("High", None)
    risk_score = round(pof_score * _COF_WEIGHT[governing_cof], 3)

    assert governing_cof == "High"
    assert risk_score == pytest.approx(14.0)
    assert _rank_from_score(risk_score) == "High"

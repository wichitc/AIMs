from datetime import date

import pytest

from app.modules.corrosion.calculation import (
    InsufficientHistoryError,
    ThicknessReading,
    compute_corrosion,
)


def test_raises_with_fewer_than_two_readings():
    with pytest.raises(InsufficientHistoryError):
        compute_corrosion(
            readings=[ThicknessReading(date(2026, 1, 1), 10.0)],
            minimum_required_thickness_mm=6.0,
            as_of=date(2026, 6, 1),
        )


def test_governing_rate_uses_the_higher_of_short_and_long_term():
    # Long-term average rate is slow (10mm -> 9mm over 5 years = 0.2mm/yr), but the most
    # recent year lost 1mm — short-term should govern per API 570/653 convention.
    readings = [
        ThicknessReading(date(2021, 1, 1), 10.0),
        ThicknessReading(date(2025, 1, 1), 9.5),
        ThicknessReading(date(2026, 1, 1), 8.5),
    ]
    result = compute_corrosion(readings, minimum_required_thickness_mm=6.0, as_of=date(2026, 1, 1))

    assert result.short_term_rate_mm_yr == pytest.approx(1.0, abs=0.01)
    assert result.long_term_rate_mm_yr == pytest.approx(0.3, abs=0.01)
    assert result.governing_rate_mm_yr == result.short_term_rate_mm_yr


def test_remaining_life_and_next_inspection_date():
    # 10mm -> 8mm over 4 years = 0.5mm/yr; min required 6mm => (8-6)/0.5 = 4 years remaining.
    readings = [
        ThicknessReading(date(2022, 1, 1), 10.0),
        ThicknessReading(date(2026, 1, 1), 8.0),
    ]
    result = compute_corrosion(readings, minimum_required_thickness_mm=6.0, as_of=date(2026, 1, 1))

    assert result.remaining_life_years == pytest.approx(4.0, abs=0.05)
    # Next inspection = min(remaining_life / 2, 10) years from as_of = 2 years -> 2028-01-01 (approx).
    assert result.next_inspection_date.year == 2028


def test_zero_corrosion_yields_indefinite_remaining_life():
    readings = [
        ThicknessReading(date(2020, 1, 1), 10.0),
        ThicknessReading(date(2026, 1, 1), 10.0),
    ]
    result = compute_corrosion(readings, minimum_required_thickness_mm=6.0, as_of=date(2026, 1, 1))

    assert result.governing_rate_mm_yr == 0
    assert result.remaining_life_years == 999.0


def test_reading_order_does_not_affect_result():
    readings_forward = [
        ThicknessReading(date(2022, 1, 1), 10.0),
        ThicknessReading(date(2026, 1, 1), 8.0),
    ]
    readings_reversed = list(reversed(readings_forward))

    result_forward = compute_corrosion(readings_forward, 6.0, date(2026, 1, 1))
    result_reversed = compute_corrosion(readings_reversed, 6.0, date(2026, 1, 1))

    assert result_forward == result_reversed

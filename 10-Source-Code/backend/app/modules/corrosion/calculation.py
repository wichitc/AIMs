"""Pure corrosion-rate / remaining-life calculation (FR-18/FR-19, API 570/653/579).

Kept dependency-free (no DB, no ORM) so it can be unit tested directly —
see tests/test_corrosion_calculation.py.
"""

from dataclasses import dataclass
from datetime import date, timedelta

DAYS_PER_YEAR = 365.25
MAX_INTERVAL_YEARS = 10  # code-maximum re-inspection interval ceiling (API 510/570)


@dataclass(frozen=True)
class ThicknessReading:
    reading_date: date
    measured_thickness_mm: float


@dataclass(frozen=True)
class CorrosionCalculationResult:
    short_term_rate_mm_yr: float
    long_term_rate_mm_yr: float
    governing_rate_mm_yr: float
    remaining_life_years: float
    next_inspection_date: date


class InsufficientHistoryError(ValueError):
    pass


def compute_corrosion(
    readings: list[ThicknessReading],
    minimum_required_thickness_mm: float,
    as_of: date,
) -> CorrosionCalculationResult:
    if len(readings) < 2:
        raise InsufficientHistoryError("At least 2 thickness readings are required to calculate corrosion rate")

    ordered = sorted(readings, key=lambda r: r.reading_date)
    latest = ordered[-1]
    previous = ordered[-2]
    earliest = ordered[0]

    short_term_years = max((latest.reading_date - previous.reading_date).days / DAYS_PER_YEAR, 1 / DAYS_PER_YEAR)
    short_term_rate = max((previous.measured_thickness_mm - latest.measured_thickness_mm) / short_term_years, 0)

    long_term_years = max((latest.reading_date - earliest.reading_date).days / DAYS_PER_YEAR, 1 / DAYS_PER_YEAR)
    long_term_rate = max((earliest.measured_thickness_mm - latest.measured_thickness_mm) / long_term_years, 0)

    # API 570/653 convention: use the more conservative (higher) of short-term vs long-term rate.
    governing_rate = max(short_term_rate, long_term_rate)

    if governing_rate <= 0:
        remaining_life = 999.0  # no measurable metal loss — effectively indefinite
    else:
        remaining_life = round(
            max((latest.measured_thickness_mm - minimum_required_thickness_mm) / governing_rate, 0), 2
        )

    interval_years = min(remaining_life / 2, MAX_INTERVAL_YEARS)
    next_inspection_date = as_of + timedelta(days=interval_years * DAYS_PER_YEAR)

    return CorrosionCalculationResult(
        short_term_rate_mm_yr=round(short_term_rate, 4),
        long_term_rate_mm_yr=round(long_term_rate, 4),
        governing_rate_mm_yr=round(governing_rate, 4),
        remaining_life_years=remaining_life,
        next_inspection_date=next_inspection_date,
    )

import uuid
from datetime import date

from pydantic import BaseModel, Field


class ThicknessRecordCreate(BaseModel):
    inspection_id: uuid.UUID | None = None
    reading_date: date
    measured_thickness_mm: float = Field(gt=0)
    measurement_method: str = Field(pattern="^(UT|RT)$")


class ThicknessRecordRead(BaseModel):
    id: uuid.UUID
    equipment_id: uuid.UUID
    reading_date: date
    measured_thickness_mm: float
    measurement_method: str

    model_config = {"from_attributes": True}


class CorrosionRecordRead(BaseModel):
    id: uuid.UUID
    equipment_id: uuid.UUID
    short_term_rate_mm_yr: float | None
    long_term_rate_mm_yr: float | None
    governing_rate_mm_yr: float
    remaining_life_years: float
    next_inspection_date: date
    calculation_basis: str | None

    model_config = {"from_attributes": True}

import uuid
from datetime import date

from pydantic import BaseModel, Field


class RiskAssessmentCreate(BaseModel):
    asset_id: uuid.UUID
    equipment_id: uuid.UUID | None = None
    methodology: str = Field(pattern="^(Qualitative|SemiQuantitative|Quantitative)$")
    pof_score: float = Field(ge=0, le=5)
    cof_financial: float | None = None
    cof_safety: str | None = Field(default=None, pattern="^(Low|Medium|High|Critical)$")
    cof_environmental: str | None = Field(default=None, pattern="^(Low|Medium|High|Critical)$")


class RiskAssessmentRead(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    methodology: str
    pof_score: float
    pof_category: str | None
    cof_category: str | None
    risk_score: float
    risk_rank: str
    recommended_interval_months: int | None
    next_inspection_date: date | None
    status: str

    model_config = {"from_attributes": True}

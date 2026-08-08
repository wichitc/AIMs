import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class InspectionPlanCreate(BaseModel):
    asset_id: uuid.UUID
    equipment_id: uuid.UUID | None = None
    plan_code: str = Field(max_length=50)
    applicable_code: str | None = None
    inspection_type: str = Field(pattern="^(Visual|UT|RT|MT|PT|PMI|Other)$")
    basis: str = Field(pattern="^(RBI|FixedInterval|Regulatory)$")
    frequency_months: int = Field(gt=0)
    next_due_date: date


class InspectionPlanRead(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    equipment_id: uuid.UUID | None
    plan_code: str
    applicable_code: str | None
    inspection_type: str
    basis: str
    frequency_months: int
    next_due_date: date
    status: str

    model_config = {"from_attributes": True}


class InspectionCreate(BaseModel):
    inspection_plan_id: uuid.UUID
    asset_id: uuid.UUID
    equipment_id: uuid.UUID | None = None
    inspector_id: uuid.UUID
    inspection_type: str
    scheduled_date: date


class InspectionUpdate(BaseModel):
    status: str | None = None
    actual_date: date | None = None


class InspectionRead(BaseModel):
    id: uuid.UUID
    inspection_plan_id: uuid.UUID
    asset_id: uuid.UUID
    equipment_id: uuid.UUID | None
    inspector_id: uuid.UUID
    inspection_type: str
    status: str
    scheduled_date: date
    actual_date: date | None

    model_config = {"from_attributes": True}


class InspectionResultCreate(BaseModel):
    checklist_item: str = Field(max_length=300)
    result_value: str | None = None
    result_status: str = Field(pattern="^(Pass|Fail|NA)$")
    remarks: str | None = None
    attachment_document_id: uuid.UUID | None = None


class InspectionResultRead(BaseModel):
    id: uuid.UUID
    checklist_item: str
    result_status: str
    recorded_at: datetime

    model_config = {"from_attributes": True}


class FindingCreate(BaseModel):
    equipment_id: uuid.UUID
    finding_type: str = Field(pattern="^(Corrosion|Crack|Leak|CoatingFailure|Deformation|Other)$")
    severity: str = Field(pattern="^(Low|Medium|High|Critical)$")
    description: str
    location_detail: str | None = None
    photo_document_id: uuid.UUID | None = None


class FindingRead(BaseModel):
    id: uuid.UUID
    inspection_id: uuid.UUID
    equipment_id: uuid.UUID
    finding_type: str
    severity: str
    status: str
    raised_date: date

    model_config = {"from_attributes": True}

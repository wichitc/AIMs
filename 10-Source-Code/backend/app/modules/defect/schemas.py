import uuid
from datetime import date

from pydantic import BaseModel, Field


class DefectCreate(BaseModel):
    finding_id: uuid.UUID
    equipment_id: uuid.UUID
    defect_type: str = Field(max_length=50)
    severity: str = Field(pattern="^(Low|Medium|High|Critical)$")
    ffs_required: bool = False
    assigned_to: uuid.UUID | None = None
    due_date: date | None = None


class DefectTransition(BaseModel):
    target_status: str = Field(pattern="^(Assessment|Approval|Repair|Verification|Closed)$")
    ffs_reference_document_id: uuid.UUID | None = None


class DefectRead(BaseModel):
    id: uuid.UUID
    finding_id: uuid.UUID
    equipment_id: uuid.UUID
    workflow_status: str
    severity: str
    ffs_required: bool
    due_date: date | None
    closed_date: date | None

    model_config = {"from_attributes": True}

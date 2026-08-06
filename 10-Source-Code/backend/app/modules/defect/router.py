import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import PaginationMeta, ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.modules.defect.schemas import DefectCreate, DefectRead, DefectTransition
from app.modules.defect.service import DefectService

router = APIRouter(tags=["Defect Management"])


@router.get("/defects", response_model=ResponseEnvelope[list[DefectRead]])
async def list_defects(
    workflow_status: str | None = None,
    assigned_to: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("defect.read")),
):
    defects, total = await DefectService(db).list_defects(
        workflow_status, assigned_to, (page - 1) * page_size, page_size
    )
    return ResponseEnvelope(
        data=[DefectRead.model_validate(d, from_attributes=True) for d in defects],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.post("/defects", response_model=ResponseEnvelope[DefectRead], status_code=201)
async def create_defect(
    payload: DefectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("defect.create")),
):
    defect = await DefectService(db).create_defect(payload, current_user.id)
    return ResponseEnvelope(data=DefectRead.model_validate(defect, from_attributes=True))


@router.get("/defects/{defect_id}", response_model=ResponseEnvelope[DefectRead])
async def get_defect(
    defect_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("defect.read")),
):
    defect = await DefectService(db).get_defect(defect_id)
    return ResponseEnvelope(data=DefectRead.model_validate(defect, from_attributes=True))


@router.put("/defects/{defect_id}", response_model=ResponseEnvelope[DefectRead])
async def transition_defect(
    defect_id: uuid.UUID,
    payload: DefectTransition,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("defect.update")),
):
    defect = await DefectService(db).transition(
        defect_id, payload.target_status, current_user.id,
        ffs_reference_document_id=payload.ffs_reference_document_id,
    )
    return ResponseEnvelope(data=DefectRead.model_validate(defect, from_attributes=True))


@router.post("/defects/{defect_id}/approve", response_model=ResponseEnvelope[DefectRead])
async def approve_defect_repair_plan(
    defect_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("defect.approve")),
):
    defect = await DefectService(db).transition(defect_id, "Repair", current_user.id)
    return ResponseEnvelope(data=DefectRead.model_validate(defect, from_attributes=True))


@router.post("/defects/{defect_id}/verify", response_model=ResponseEnvelope[DefectRead])
async def verify_and_close_defect(
    defect_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("defect.update")),
):
    defect = await DefectService(db).transition(defect_id, "Closed", current_user.id)
    return ResponseEnvelope(data=DefectRead.model_validate(defect, from_attributes=True))

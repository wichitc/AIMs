import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import PaginationMeta, ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.modules.inspection.schemas import (
    FindingCreate,
    FindingRead,
    InspectionCreate,
    InspectionPlanCreate,
    InspectionPlanRead,
    InspectionRead,
    InspectionResultCreate,
    InspectionResultRead,
)
from app.modules.inspection.service import FindingService, InspectionPlanService, InspectionService

router = APIRouter(tags=["Inspection Management"])


@router.get("/inspection-plans", response_model=ResponseEnvelope[list[InspectionPlanRead]])
async def list_inspection_plans(
    asset_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inspection.read")),
):
    plans, total = await InspectionPlanService(db).list_plans(asset_id, page, page_size)
    return ResponseEnvelope(
        data=[InspectionPlanRead.model_validate(p, from_attributes=True) for p in plans],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.post("/inspection-plans", response_model=ResponseEnvelope[InspectionPlanRead], status_code=201)
async def create_inspection_plan(
    payload: InspectionPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inspection.create")),
):
    plan = await InspectionPlanService(db).create_plan(payload, current_user.id)
    return ResponseEnvelope(data=InspectionPlanRead.model_validate(plan, from_attributes=True))


@router.get("/inspections", response_model=ResponseEnvelope[list[InspectionRead]])
async def list_inspections(
    status: str | None = None,
    inspector_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inspection.read")),
):
    inspections, total = await InspectionService(db).list_inspections(status, inspector_id, page, page_size)
    return ResponseEnvelope(
        data=[InspectionRead.model_validate(i, from_attributes=True) for i in inspections],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.post("/inspections", response_model=ResponseEnvelope[InspectionRead], status_code=201)
async def schedule_inspection(
    payload: InspectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inspection.create")),
):
    inspection = await InspectionService(db).schedule_inspection(payload, current_user.id)
    return ResponseEnvelope(data=InspectionRead.model_validate(inspection, from_attributes=True))


@router.get("/inspections/{inspection_id}", response_model=ResponseEnvelope[InspectionRead])
async def get_inspection(
    inspection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inspection.read")),
):
    inspection = await InspectionService(db).get_inspection(inspection_id)
    return ResponseEnvelope(data=InspectionRead.model_validate(inspection, from_attributes=True))


@router.post(
    "/inspections/{inspection_id}/results",
    response_model=ResponseEnvelope[InspectionResultRead],
    status_code=201,
)
async def submit_result(
    inspection_id: uuid.UUID,
    payload: InspectionResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inspection.execute")),
):
    result = await InspectionService(db).submit_result(inspection_id, payload, current_user.id)
    return ResponseEnvelope(data=InspectionResultRead.model_validate(result, from_attributes=True))


@router.post(
    "/inspections/{inspection_id}/findings", response_model=ResponseEnvelope[FindingRead], status_code=201
)
async def raise_finding(
    inspection_id: uuid.UUID,
    payload: FindingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inspection.execute")),
):
    finding = await InspectionService(db).raise_finding(inspection_id, payload, current_user.id)
    return ResponseEnvelope(data=FindingRead.model_validate(finding, from_attributes=True))


@router.post("/inspections/{inspection_id}/complete", response_model=ResponseEnvelope[InspectionRead])
async def complete_inspection(
    inspection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inspection.execute")),
):
    inspection = await InspectionService(db).complete_inspection(inspection_id, current_user.id)
    return ResponseEnvelope(data=InspectionRead.model_validate(inspection, from_attributes=True))


@router.get("/findings", response_model=ResponseEnvelope[list[FindingRead]])
async def list_findings(
    status: str | None = None,
    equipment_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inspection.read")),
):
    findings, total = await FindingService(db).list_findings(status, equipment_id, page, page_size)
    return ResponseEnvelope(
        data=[FindingRead.model_validate(f, from_attributes=True) for f in findings],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )

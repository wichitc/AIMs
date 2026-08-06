import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import PaginationMeta, ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.modules.rbi.schemas import RiskAssessmentCreate, RiskAssessmentRead
from app.modules.rbi.service import RiskAssessmentService

router = APIRouter(tags=["Risk Based Inspection"])


@router.get("/risk-assessments", response_model=ResponseEnvelope[list[RiskAssessmentRead]])
async def list_risk_assessments(
    asset_id: uuid.UUID | None = None,
    risk_rank: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("risk.read")),
):
    items, total = await RiskAssessmentService(db).list_assessments(
        asset_id, risk_rank, (page - 1) * page_size, page_size
    )
    return ResponseEnvelope(
        data=[RiskAssessmentRead.model_validate(i, from_attributes=True) for i in items],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.post("/risk-assessments", response_model=ResponseEnvelope[RiskAssessmentRead], status_code=201)
async def create_risk_assessment(
    payload: RiskAssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("risk.create")),
):
    assessment = await RiskAssessmentService(db).create_assessment(payload, current_user.id)
    return ResponseEnvelope(data=RiskAssessmentRead.model_validate(assessment, from_attributes=True))


@router.get("/risk-assessments/{assessment_id}", response_model=ResponseEnvelope[RiskAssessmentRead])
async def get_risk_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("risk.read")),
):
    assessment = await RiskAssessmentService(db).get_assessment(assessment_id)
    return ResponseEnvelope(data=RiskAssessmentRead.model_validate(assessment, from_attributes=True))


@router.post("/risk-assessments/{assessment_id}/approve", response_model=ResponseEnvelope[RiskAssessmentRead])
async def approve_risk_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("risk.approve")),
):
    assessment = await RiskAssessmentService(db).approve(assessment_id, current_user.id)
    return ResponseEnvelope(data=RiskAssessmentRead.model_validate(assessment, from_attributes=True))

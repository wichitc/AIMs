import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import write_audit_log
from app.core.exceptions import NotFoundError
from app.modules.asset.models import Asset
from app.modules.rbi.models import RiskAssessment
from app.modules.rbi.schemas import RiskAssessmentCreate

# COF category → numeric weight (API 580 qualitative consequence banding: A=lowest .. E=highest)
_COF_WEIGHT = {"Low": 1.0, "Medium": 2.0, "High": 3.5, "Critical": 5.0}
_COF_CATEGORY = {"Low": "A", "Medium": "B", "High": "D", "Critical": "E"}

# Risk rank → recommended re-inspection interval (months), per API 580 risk matrix convention
_INTERVAL_BY_RANK = {"Low": 72, "Medium": 48, "High": 24, "VeryHigh": 12}


def _governing_cof(safety: str | None, environmental: str | None) -> str:
    order = ["Low", "Medium", "High", "Critical"]
    candidates = [c for c in (safety, environmental) if c]
    if not candidates:
        return "Medium"
    return max(candidates, key=order.index)


def _rank_from_score(score: float) -> str:
    if score >= 15:
        return "VeryHigh"
    if score >= 8:
        return "High"
    if score >= 3:
        return "Medium"
    return "Low"


def _pof_category(pof_score: float) -> str:
    """Buckets the continuous 0-5 POF score into the 5x5 risk-matrix category (1=lowest .. 5=highest)."""
    return str(min(5, max(1, round(pof_score))))


class RiskAssessmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_asset(self, asset_id: uuid.UUID) -> Asset:
        asset = (
            await self.db.execute(select(Asset).where(Asset.id == asset_id, Asset.is_deleted.is_(False)))
        ).scalar_one_or_none()
        if not asset:
            raise NotFoundError(f"Asset {asset_id} not found")
        return asset

    async def create_assessment(self, payload: RiskAssessmentCreate, actor_id: str | None) -> RiskAssessment:
        asset = await self._get_asset(payload.asset_id)

        governing_cof = _governing_cof(payload.cof_safety, payload.cof_environmental)
        cof_weight = _COF_WEIGHT[governing_cof]
        risk_score = round(payload.pof_score * cof_weight, 3)
        risk_rank = _rank_from_score(risk_score)
        interval_months = _INTERVAL_BY_RANK[risk_rank]

        assessment = RiskAssessment(
            asset_id=payload.asset_id,
            equipment_id=payload.equipment_id,
            assessment_date=date.today(),
            methodology=payload.methodology,
            pof_score=payload.pof_score,
            pof_category=_pof_category(payload.pof_score),
            cof_financial=payload.cof_financial,
            cof_safety=payload.cof_safety,
            cof_environmental=payload.cof_environmental,
            cof_category=_COF_CATEGORY[governing_cof],
            risk_score=risk_score,
            risk_rank=risk_rank,
            recommended_interval_months=interval_months,
            next_inspection_date=date.today() + timedelta(days=interval_months * 30),
            assessed_by=uuid.UUID(actor_id) if actor_id else None,
            status="Draft",
        )
        self.db.add(assessment)
        await self.db.flush()

        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(asset.org_id), action="Create", entity_type="RiskAssessment",
            entity_id=assessment.id, new_value={"risk_score": risk_score, "risk_rank": risk_rank},
        )
        await self.db.commit()
        return assessment

    async def get_assessment(self, assessment_id: uuid.UUID) -> RiskAssessment:
        assessment = (
            await self.db.execute(select(RiskAssessment).where(RiskAssessment.id == assessment_id))
        ).scalar_one_or_none()
        if not assessment:
            raise NotFoundError(f"Risk assessment {assessment_id} not found")
        return assessment

    async def list_assessments(
        self, asset_id: uuid.UUID | None, risk_rank: str | None, offset: int, limit: int
    ) -> tuple[list[RiskAssessment], int]:
        stmt = select(RiskAssessment)
        if asset_id:
            stmt = stmt.where(RiskAssessment.asset_id == asset_id)
        if risk_rank:
            stmt = stmt.where(RiskAssessment.risk_rank == risk_rank)
        total = len((await self.db.execute(stmt)).scalars().all())
        rows = (await self.db.execute(stmt.offset(offset).limit(limit))).scalars().all()
        return list(rows), total

    async def approve(self, assessment_id: uuid.UUID, actor_id: str | None) -> RiskAssessment:
        assessment = await self.get_assessment(assessment_id)
        assessment.status = "Approved"
        assessment.approved_by = uuid.UUID(actor_id) if actor_id else None
        await write_audit_log(
            self.db, user_id=actor_id, org_id=None, action="Approve", entity_type="RiskAssessment",
            entity_id=assessment.id, new_value={"status": "Approved"},
        )
        await self.db.commit()
        return assessment

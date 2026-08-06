import uuid
from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import write_audit_log
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.modules.inspection.models import Finding, Inspection, InspectionPlan, InspectionResult
from app.modules.inspection.repository import InspectionPlanRepository, InspectionRepository
from app.modules.inspection.schemas import (
    FindingCreate,
    InspectionCreate,
    InspectionPlanCreate,
    InspectionResultCreate,
)


class InspectionPlanService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = InspectionPlanRepository(db)

    async def create_plan(self, payload: InspectionPlanCreate, actor_id: str | None) -> InspectionPlan:
        if await self.repo.get_by_code(payload.plan_code):
            raise ConflictError(f"Inspection plan code '{payload.plan_code}' already exists")

        plan = InspectionPlan(**payload.model_dump())
        self.repo.add(plan)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=None, action="Create", entity_type="InspectionPlan",
            entity_id=plan.id, new_value={"plan_code": plan.plan_code},
        )
        await self.db.commit()
        return plan

    async def list_plans(self, asset_id: uuid.UUID | None, page: int, page_size: int):
        return await self.repo.list_all(asset_id, (page - 1) * page_size, page_size)


class InspectionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.inspections = InspectionRepository(db)
        self.plans = InspectionPlanRepository(db)

    async def schedule_inspection(self, payload: InspectionCreate, actor_id: str | None) -> Inspection:
        plan = await self.plans.get_by_id(payload.inspection_plan_id)
        if not plan:
            raise NotFoundError(f"Inspection plan {payload.inspection_plan_id} not found")

        inspection = Inspection(status="Planned", **payload.model_dump())
        self.inspections.add(inspection)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=None, action="Create", entity_type="Inspection",
            entity_id=inspection.id, new_value={"scheduled_date": str(inspection.scheduled_date)},
        )
        await self.db.commit()
        return inspection

    async def get_inspection(self, inspection_id: uuid.UUID) -> Inspection:
        inspection = await self.inspections.get_by_id(inspection_id)
        if not inspection:
            raise NotFoundError(f"Inspection {inspection_id} not found")
        return inspection

    async def list_inspections(self, status: str | None, inspector_id: uuid.UUID | None, page: int, page_size: int):
        return await self.inspections.list_all(status, inspector_id, (page - 1) * page_size, page_size)

    async def submit_result(
        self, inspection_id: uuid.UUID, payload: InspectionResultCreate, actor_id: str | None
    ) -> InspectionResult:
        inspection = await self.get_inspection(inspection_id)
        if inspection.status == "Completed":
            raise BusinessRuleError("Cannot add results to a completed inspection")

        result = InspectionResult(
            inspection_id=inspection_id,
            recorded_at=datetime.now(timezone.utc),
            recorded_by=uuid.UUID(actor_id) if actor_id else None,
            **payload.model_dump(),
        )
        self.inspections.add_result(result)
        if inspection.status == "Planned":
            inspection.status = "InProgress"
        await self.db.flush()
        await self.db.commit()
        return result

    async def raise_finding(
        self, inspection_id: uuid.UUID, payload: FindingCreate, actor_id: str | None
    ) -> Finding:
        inspection = await self.get_inspection(inspection_id)

        finding = Finding(
            inspection_id=inspection_id,
            status="Open",
            raised_by=uuid.UUID(actor_id) if actor_id else uuid.uuid4(),
            raised_date=date.today(),
            **payload.model_dump(),
        )
        self.inspections.add_finding(finding)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=None, action="Create", entity_type="Finding",
            entity_id=finding.id, new_value={"severity": finding.severity, "finding_type": finding.finding_type},
        )
        await self.db.commit()
        return finding

    async def complete_inspection(self, inspection_id: uuid.UUID, actor_id: str | None) -> Inspection:
        inspection = await self.get_inspection(inspection_id)
        if inspection.status == "Completed":
            raise BusinessRuleError("Inspection is already completed")
        if inspection.status == "Cancelled":
            raise BusinessRuleError("Cannot complete a cancelled inspection")

        inspection.status = "Completed"
        inspection.actual_date = inspection.actual_date or date.today()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=None, action="Update", entity_type="Inspection",
            entity_id=inspection.id, new_value={"status": "Completed"},
        )
        await self.db.commit()
        return inspection

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import write_audit_log
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.modules.defect.models import Defect
from app.modules.defect.schemas import DefectCreate

# FR-21: Finding -> Assessment -> Approval -> Repair -> Verification -> Closed
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "Finding": {"Assessment"},
    "Assessment": {"Approval"},
    "Approval": {"Repair"},
    "Repair": {"Verification"},
    "Verification": {"Closed", "Repair"},  # failed verification sends it back to Repair
    "Closed": set(),
}


class DefectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_defect(self, payload: DefectCreate, actor_id: str | None) -> Defect:
        defect = Defect(workflow_status="Finding", **payload.model_dump())
        self.db.add(defect)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=None, action="Create", entity_type="Defect",
            entity_id=defect.id, new_value={"severity": defect.severity},
        )
        await self.db.commit()
        return defect

    async def get_defect(self, defect_id: uuid.UUID) -> Defect:
        defect = (await self.db.execute(select(Defect).where(Defect.id == defect_id))).scalar_one_or_none()
        if not defect:
            raise NotFoundError(f"Defect {defect_id} not found")
        return defect

    async def list_defects(
        self, workflow_status: str | None, assigned_to: uuid.UUID | None, offset: int, limit: int
    ) -> tuple[list[Defect], int]:
        stmt = select(Defect)
        if workflow_status:
            stmt = stmt.where(Defect.workflow_status == workflow_status)
        if assigned_to:
            stmt = stmt.where(Defect.assigned_to == assigned_to)
        total = len((await self.db.execute(stmt)).scalars().all())
        rows = (await self.db.execute(stmt.offset(offset).limit(limit))).scalars().all()
        return list(rows), total

    async def transition(self, defect_id: uuid.UUID, target_status: str, actor_id: str | None, **extra) -> Defect:
        defect = await self.get_defect(defect_id)
        allowed = _VALID_TRANSITIONS.get(defect.workflow_status, set())
        if target_status not in allowed:
            raise BusinessRuleError(
                f"Invalid workflow transition: {defect.workflow_status} -> {target_status}",
                details=[{"field": "workflow_status", "issue": "invalid_transition"}],
            )

        defect.workflow_status = target_status
        if extra.get("ffs_reference_document_id"):
            defect.ffs_reference_document_id = extra["ffs_reference_document_id"]
        if target_status == "Closed":
            defect.closed_date = date.today()

        await write_audit_log(
            self.db, user_id=actor_id, org_id=None, action="Update", entity_type="Defect",
            entity_id=defect.id, new_value={"workflow_status": target_status},
        )
        await self.db.commit()
        return defect

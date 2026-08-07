import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.inspection.models import Finding, Inspection, InspectionPlan, InspectionResult


class InspectionPlanRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_code(self, plan_code: str) -> InspectionPlan | None:
        stmt = select(InspectionPlan).where(InspectionPlan.plan_code == plan_code)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, plan_id: uuid.UUID) -> InspectionPlan | None:
        return (
            await self.db.execute(select(InspectionPlan).where(InspectionPlan.id == plan_id))
        ).scalar_one_or_none()

    async def list_all(self, asset_id: uuid.UUID | None, offset: int, limit: int) -> tuple[list[InspectionPlan], int]:
        stmt = select(InspectionPlan)
        if asset_id:
            stmt = stmt.where(InspectionPlan.asset_id == asset_id)
        total = len((await self.db.execute(stmt)).scalars().all())
        rows = (await self.db.execute(stmt.offset(offset).limit(limit))).scalars().all()
        return list(rows), total

    def add(self, plan: InspectionPlan) -> None:
        self.db.add(plan)


class InspectionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, inspection_id: uuid.UUID) -> Inspection | None:
        stmt = (
            select(Inspection)
            .where(Inspection.id == inspection_id)
            .options(selectinload(Inspection.results), selectinload(Inspection.findings))
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_all(
        self, status: str | None, inspector_id: uuid.UUID | None, offset: int, limit: int
    ) -> tuple[list[Inspection], int]:
        stmt = select(Inspection)
        if status:
            stmt = stmt.where(Inspection.status == status)
        if inspector_id:
            stmt = stmt.where(Inspection.inspector_id == inspector_id)
        total = len((await self.db.execute(stmt)).scalars().all())
        rows = (await self.db.execute(stmt.offset(offset).limit(limit))).scalars().all()
        return list(rows), total

    def add(self, inspection: Inspection) -> None:
        self.db.add(inspection)

    def add_result(self, result: InspectionResult) -> None:
        self.db.add(result)

    def add_finding(self, finding: Finding) -> None:
        self.db.add(finding)


class FindingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, finding_id: uuid.UUID) -> Finding | None:
        return (await self.db.execute(select(Finding).where(Finding.id == finding_id))).scalar_one_or_none()

    async def list_all(
        self, status: str | None, equipment_id: uuid.UUID | None, offset: int, limit: int
    ) -> tuple[list[Finding], int]:
        stmt = select(Finding)
        if status:
            stmt = stmt.where(Finding.status == status)
        if equipment_id:
            stmt = stmt.where(Finding.equipment_id == equipment_id)
        stmt = stmt.order_by(Finding.raised_date.desc())
        total = len((await self.db.execute(stmt)).scalars().all())
        rows = (await self.db.execute(stmt.offset(offset).limit(limit))).scalars().all()
        return list(rows), total

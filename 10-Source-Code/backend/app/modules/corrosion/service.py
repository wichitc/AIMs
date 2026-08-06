import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import write_audit_log
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.modules.asset.models import Equipment
from app.modules.corrosion.calculation import (
    InsufficientHistoryError,
    ThicknessReading,
    compute_corrosion,
)
from app.modules.corrosion.models import CorrosionRecord, ThicknessRecord
from app.modules.corrosion.schemas import ThicknessRecordCreate


class ThicknessRecordService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_reading(
        self, equipment_id: uuid.UUID, payload: ThicknessRecordCreate, actor_id: str | None
    ) -> ThicknessRecord:
        record = ThicknessRecord(equipment_id=equipment_id, **payload.model_dump())
        self.db.add(record)
        await self.db.flush()
        await self.db.commit()
        return record

    async def list_readings(self, equipment_id: uuid.UUID) -> list[ThicknessRecord]:
        stmt = (
            select(ThicknessRecord)
            .where(ThicknessRecord.equipment_id == equipment_id)
            .order_by(ThicknessRecord.reading_date.asc())
        )
        return list((await self.db.execute(stmt)).scalars().all())


class CorrosionCalculationService:
    """Implements FR-18/FR-19: corrosion rate and remaining-life calculation per API 570/653/579."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.readings = ThicknessRecordService(db)

    async def _get_equipment(self, equipment_id: uuid.UUID) -> Equipment:
        equipment = (
            await self.db.execute(select(Equipment).where(Equipment.id == equipment_id))
        ).scalar_one_or_none()
        if not equipment:
            raise NotFoundError(f"Equipment {equipment_id} not found")
        return equipment

    async def calculate(self, equipment_id: uuid.UUID, actor_id: str | None) -> CorrosionRecord:
        equipment = await self._get_equipment(equipment_id)
        readings = await self.readings.list_readings(equipment_id)

        try:
            result = compute_corrosion(
                readings=[ThicknessReading(r.reading_date, float(r.measured_thickness_mm)) for r in readings],
                minimum_required_thickness_mm=float(equipment.minimum_required_thickness_mm or 0),
                as_of=date.today(),
            )
        except InsufficientHistoryError as exc:
            raise BusinessRuleError(
                str(exc), details=[{"field": "thickness_record", "issue": "insufficient_history"}]
            ) from exc

        record = CorrosionRecord(
            equipment_id=equipment_id,
            assessment_date=date.today(),
            short_term_rate_mm_yr=result.short_term_rate_mm_yr,
            long_term_rate_mm_yr=result.long_term_rate_mm_yr,
            governing_rate_mm_yr=result.governing_rate_mm_yr,
            remaining_life_years=result.remaining_life_years,
            next_inspection_date=result.next_inspection_date,
            calculation_basis="API 570 / API 653",
            calculated_by=uuid.UUID(actor_id) if actor_id else None,
        )
        self.db.add(record)
        await self.db.flush()

        await write_audit_log(
            self.db, user_id=actor_id, org_id=None, action="Create", entity_type="CorrosionRecord",
            entity_id=record.id,
            new_value={
                "governing_rate_mm_yr": result.governing_rate_mm_yr,
                "remaining_life_years": result.remaining_life_years,
            },
        )
        await self.db.commit()
        return record

    async def list_records(self, equipment_id: uuid.UUID) -> list[CorrosionRecord]:
        stmt = (
            select(CorrosionRecord)
            .where(CorrosionRecord.equipment_id == equipment_id)
            .order_by(CorrosionRecord.assessment_date.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

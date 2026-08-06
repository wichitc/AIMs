import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base_model import AuditMixin, UUIDMixin
from app.core.database import Base


class ThicknessRecord(Base, UUIDMixin, AuditMixin):
    __tablename__ = "thickness_record"

    equipment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False)
    inspection_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("inspection.id"))
    reading_date: Mapped[date] = mapped_column(Date, nullable=False)
    measured_thickness_mm: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    measurement_method: Mapped[str] = mapped_column(String(20), nullable=False)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))


class CorrosionRecord(Base, UUIDMixin, AuditMixin):
    __tablename__ = "corrosion_record"

    equipment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False)
    assessment_date: Mapped[date] = mapped_column(Date, nullable=False)
    short_term_rate_mm_yr: Mapped[float | None] = mapped_column(Numeric(8, 4))
    long_term_rate_mm_yr: Mapped[float | None] = mapped_column(Numeric(8, 4))
    governing_rate_mm_yr: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    remaining_life_years: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    next_inspection_date: Mapped[date] = mapped_column(Date, nullable=False)
    calculation_basis: Mapped[str | None] = mapped_column(String(50))
    calculated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))

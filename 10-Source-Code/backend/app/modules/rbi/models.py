import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base_model import AuditMixin, UUIDMixin
from app.core.database import Base


class RiskAssessment(Base, UUIDMixin, AuditMixin):
    __tablename__ = "risk_assessment"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("asset.id"), nullable=False)
    equipment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("equipment.id"))
    assessment_date: Mapped[date] = mapped_column(Date, nullable=False)
    methodology: Mapped[str] = mapped_column(String(20), nullable=False)
    pof_score: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)
    pof_category: Mapped[str | None] = mapped_column(String(1))
    cof_financial: Mapped[float | None] = mapped_column(Numeric(14, 2))
    cof_safety: Mapped[str | None] = mapped_column(String(20))
    cof_environmental: Mapped[str | None] = mapped_column(String(20))
    cof_category: Mapped[str | None] = mapped_column(String(1))
    risk_score: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    risk_rank: Mapped[str] = mapped_column(String(20), nullable=False)
    recommended_interval_months: Mapped[int | None] = mapped_column(Integer)
    next_inspection_date: Mapped[date | None] = mapped_column(Date)
    assessed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Draft")

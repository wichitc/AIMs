import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.base_model import AuditMixin, UUIDMixin
from app.core.database import Base


class InspectionPlan(Base, UUIDMixin, AuditMixin):
    __tablename__ = "inspection_plan"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("asset.id"), nullable=False)
    equipment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("equipment.id"))
    plan_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    applicable_code: Mapped[str | None] = mapped_column(String(50))
    inspection_type: Mapped[str] = mapped_column(String(30), nullable=False)
    basis: Mapped[str] = mapped_column(String(20), nullable=False)
    frequency_months: Mapped[int] = mapped_column(Integer, nullable=False)
    next_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Active")

    inspections: Mapped[list["Inspection"]] = relationship(back_populates="plan")


class Inspection(Base, UUIDMixin, AuditMixin):
    __tablename__ = "inspection"

    inspection_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inspection_plan.id"), nullable=False
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("asset.id"), nullable=False)
    equipment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("equipment.id"))
    inspector_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    inspection_type: Mapped[str] = mapped_column(String(30), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Planned")

    plan: Mapped["InspectionPlan"] = relationship(back_populates="inspections")
    results: Mapped[list["InspectionResult"]] = relationship(back_populates="inspection", cascade="all, delete-orphan")
    findings: Mapped[list["Finding"]] = relationship(back_populates="inspection", cascade="all, delete-orphan")


class InspectionResult(Base, UUIDMixin, AuditMixin):
    __tablename__ = "inspection_result"

    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inspection.id", ondelete="CASCADE"), nullable=False
    )
    checklist_item: Mapped[str] = mapped_column(String(300), nullable=False)
    result_value: Mapped[str | None] = mapped_column(String(500))
    result_status: Mapped[str] = mapped_column(String(10), nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text)
    attachment_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("document.id"))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))

    inspection: Mapped["Inspection"] = relationship(back_populates="results")


class Finding(Base, UUIDMixin, AuditMixin):
    __tablename__ = "finding"

    inspection_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inspection.id"), nullable=False)
    equipment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False)
    finding_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location_detail: Mapped[str | None] = mapped_column(String(300))
    photo_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("document.id"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Open")
    raised_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    raised_date: Mapped[date] = mapped_column(Date, nullable=False)

    inspection: Mapped["Inspection"] = relationship(back_populates="findings")

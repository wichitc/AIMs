import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base_model import AuditMixin, UUIDMixin
from app.core.database import Base


class Defect(Base, UUIDMixin, AuditMixin):
    __tablename__ = "defect"

    finding_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("finding.id"), nullable=False)
    equipment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False)
    defect_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    workflow_status: Mapped[str] = mapped_column(String(20), nullable=False, default="Finding")
    ffs_required: Mapped[bool] = mapped_column(Boolean, default=False)
    ffs_reference_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("document.id"))
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))
    due_date: Mapped[date | None] = mapped_column(Date)
    closed_date: Mapped[date | None] = mapped_column(Date)

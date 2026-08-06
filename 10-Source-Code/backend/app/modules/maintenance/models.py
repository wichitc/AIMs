import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base_model import AuditMixin, UUIDMixin
from app.core.database import Base


class MaintenanceOrder(Base, UUIDMixin, AuditMixin):
    __tablename__ = "maintenance_order"

    equipment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False)
    defect_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("defect.id"))
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="Medium")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Open")
    scheduled_date: Mapped[date | None] = mapped_column(Date)
    completed_date: Mapped[date | None] = mapped_column(Date)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))
    cost_estimate: Mapped[float | None] = mapped_column(Numeric(14, 2))

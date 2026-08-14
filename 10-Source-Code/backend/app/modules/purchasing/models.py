import uuid

from sqlalchemy import Boolean, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.base_model import AuditMixin, SoftDeleteMixin, UUIDMixin
from app.core.database import Base


class Material(Base, UUIDMixin, AuditMixin, SoftDeleteMixin):
    """Spare-part / consumable catalog entry (SAP MM FR-002, simplified — no separate
    material_types/material_plants/uom_conversions tables; AIMS has one plant-equivalent
    scope per org, not SAP's multi-plant valuation-area model)."""

    __tablename__ = "material"
    __table_args__ = (UniqueConstraint("org_id", "material_number", name="uq_material_org_number"),)

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=False)
    material_number: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    material_type: Mapped[str] = mapped_column(String(30), nullable=False)  # SparePart|Consumable|RawMaterial|Service
    material_group: Mapped[str | None] = mapped_column(String(100))
    base_uom: Mapped[str] = mapped_column(String(10), nullable=False)  # EA, KG, M, L, ...
    moving_average_price: Mapped[float | None] = mapped_column(Numeric(14, 2))
    min_stock_level: Mapped[float | None] = mapped_column(Numeric(14, 3))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Supplier(Base, UUIDMixin, AuditMixin, SoftDeleteMixin):
    """Vendor master (SAP MM FR-003, simplified — one purchasing-org scope per org, a single
    `is_blocked` flag instead of the separate global/org/material supplier_blocks table)."""

    __tablename__ = "supplier"
    __table_args__ = (UniqueConstraint("org_id", "supplier_number", name="uq_supplier_org_number"),)

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=False)
    supplier_number: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(String)
    payment_terms: Mapped[str | None] = mapped_column(String(100))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    block_reason: Mapped[str | None] = mapped_column(String(300))

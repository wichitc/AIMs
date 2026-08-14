import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

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


class PurchasingInfoRecord(Base, UUIDMixin, AuditMixin):
    """Supplier-material commercial relationship (SAP MM FR-005, simplified — one price per
    record, no separate conditions/condition_scales quantity-break tables)."""

    __tablename__ = "purchasing_info_record"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=False)
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("material.id"), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier.id"), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    lead_time_days: Mapped[int | None] = mapped_column()
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SourceListEntry(Base, UUIDMixin, AuditMixin):
    """Eligible/fixed/blocked supplier declaration for a material (SAP MM FR-009
    source_list_entries, simplified — one org scope, no plant-level shadowing)."""

    __tablename__ = "source_list_entry"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=False)
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("material.id"), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier.id"), nullable=False)
    is_fixed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)


class QuotaArrangement(Base, UUIDMixin, AuditMixin):
    """Static supplier-split preference for a material (SAP MM FR-009 quota_arrangements,
    simplified to a fixed percentage weight — no running allocated_qty consumption tracking
    across POs, which would require quota state to update on every PO conversion; deferred to
    a later stage if actual rotation-by-consumption is needed)."""

    __tablename__ = "quota_arrangement"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=False)
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("material.id"), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier.id"), nullable=False)
    quota_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)


class PurchaseRequisition(Base, UUIDMixin, AuditMixin):
    """Demand capture and single-step approval (SAP MM FR-006/FR-007, simplified — one
    release step instead of a configurable multi-step delegation/escalation workflow engine,
    matching AIMS's existing Defect/Risk/Asset approve pattern). Identified by id like every
    other AIMS entity, not a configurable number-range engine.

    maintenance_order_id/defect_id are an AIMS-specific integration point beyond the SAP MM
    spec: a repair that needs parts can originate a PR directly."""

    __tablename__ = "purchase_requisition"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=False)
    requester_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Draft")
    requested_date: Mapped[date] = mapped_column(Date, nullable=False)
    required_date: Mapped[date | None] = mapped_column(Date)
    maintenance_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("maintenance_order.id")
    )
    defect_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("defect.id"))
    decision_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_reason: Mapped[str | None] = mapped_column(String(500))

    items: Mapped[list["PurchaseRequisitionItem"]] = relationship(
        back_populates="requisition", cascade="all, delete-orphan"
    )


class PurchaseRequisitionItem(Base, UUIDMixin, AuditMixin):
    __tablename__ = "purchase_requisition_item"

    purchase_requisition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_requisition.id"), nullable=False
    )
    line_no: Mapped[int] = mapped_column(nullable=False)
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("material.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    estimated_price: Mapped[float | None] = mapped_column(Numeric(14, 2))
    required_date: Mapped[date | None] = mapped_column(Date)

    requisition: Mapped["PurchaseRequisition"] = relationship(back_populates="items")

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


class RFQ(Base, UUIDMixin, AuditMixin):
    """SAP MM FR-008, simplified — an RFQ inherits its requested lines 1:1 from the
    Approved purchase requisition it references, rather than a separate rfq_items table
    ("copy referenced PR" per FR-008); dispatch is symbolic (status flag + timestamped
    invites), not a real email/PDF output — matches this build's "no legal output
    templates/providers" simplification."""

    __tablename__ = "rfq"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=False)
    purchase_requisition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_requisition.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Draft")  # Draft|Dispatched|Closed
    deadline: Mapped[date | None] = mapped_column(Date)


class RFQSupplierInvite(Base, UUIDMixin, AuditMixin):
    __tablename__ = "rfq_supplier_invite"
    __table_args__ = (UniqueConstraint("rfq_id", "supplier_id", name="uq_rfq_supplier_invite"),)

    rfq_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rfq.id"), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier.id"), nullable=False)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Quotation(Base, UUIDMixin, AuditMixin):
    """A supplier's recorded bid against an RFQ (SAP MM FR-008). AIMS has no external
    supplier portal, so the buyer records the quotation on the supplier's behalf."""

    __tablename__ = "quotation"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=False)
    rfq_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rfq.id"), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier.id"), nullable=False)
    submitted_date: Mapped[date] = mapped_column(Date, nullable=False)

    items: Mapped[list["QuotationItem"]] = relationship(back_populates="quotation", cascade="all, delete-orphan")


class QuotationItem(Base, UUIDMixin, AuditMixin):
    __tablename__ = "quotation_item"

    quotation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quotation.id"), nullable=False)
    pr_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_requisition_item.id"), nullable=False
    )
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("material.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    is_awarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    quotation: Mapped["Quotation"] = relationship(back_populates="items")


class PurchaseOrder(Base, UUIDMixin, AuditMixin):
    """SAP MM FR-010, simplified lifecycle — Draft -> Approved -> Sent (dispatch is
    symbolic, same simplification as RFQ). confirmed_date/confirmed_by_supplier collapse
    SAP's separate per-schedule-line supplier_confirmations table into two header fields —
    "was this order confirmed, and when" is enough signal for AIMS's context."""

    __tablename__ = "purchase_order"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("supplier.id"), nullable=False)
    purchase_requisition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_requisition.id")
    )
    rfq_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("rfq.id"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Draft")
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))
    confirmed_date: Mapped[date | None] = mapped_column(Date)
    confirmed_by_supplier: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    items: Mapped[list["PurchaseOrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class PurchaseOrderItem(Base, UUIDMixin, AuditMixin):
    __tablename__ = "purchase_order_item"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_order.id"), nullable=False
    )
    line_no: Mapped[int] = mapped_column(nullable=False)
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("material.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    received_quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    pr_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_requisition_item.id")
    )

    order: Mapped["PurchaseOrder"] = relationship(back_populates="items")

"""Inventory posting core (SAP MM FR-015/FR-016/FR-017, ADR-0008, simplified for AIMS —
single valuation context, moving-average price only, no fiscal periods/GL integration/
tolerance policy). One posting path (MovementPostingService in service.py) creates an
immutable MaterialDocument, appends to the StockLedger, and updates the derived
StockBalance atomically — the same "one posting engine" principle ADR-0008 documents,
scaled down. Storage locations reuse AIMS's existing asset.Location (Plant/Area/Unit)
hierarchy rather than introducing a separate plant/storage-location model."""

import uuid
from datetime import date, datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.base_model import AuditMixin, UUIDMixin
from app.core.database import Base


class MaterialDocument(Base, UUIDMixin, AuditMixin):
    """Immutable posted movement header. Never updated after creation — corrections are
    modeled as a new reversing document (movement 102 references the original via
    reversal_of_id), never a mutation of the original."""

    __tablename__ = "material_document"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 101 GR | 102 GR reversal | ...
    posted_date: Mapped[date] = mapped_column(nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(30))  # "PurchaseOrder" | ...
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    reversal_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("material_document.id", use_alter=True, name="fk_material_document_reversal")
    )

    items: Mapped[list["MaterialDocumentItem"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class MaterialDocumentItem(Base, UUIDMixin, AuditMixin):
    __tablename__ = "material_document_item"

    material_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("material_document.id"), nullable=False
    )
    line_no: Mapped[int] = mapped_column(nullable=False)
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("material.id"), nullable=False)
    storage_location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("location.id"), nullable=False
    )
    # Signed: positive for a receipt, negative for a reversal/issue — matches SAP's signed
    # quantity convention so the stock ledger can be summed directly (FR-017).
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    po_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_order_item.id")
    )

    document: Mapped["MaterialDocument"] = relationship(back_populates="items")


class StockLedger(Base, UUIDMixin):
    """Append-only. Never updated or deleted — a reversal appends a new negative entry,
    it never touches the original row (cross-feature acceptance rule: "stock balance
    equals the signed sum of the stock ledger for the same dimensions")."""

    __tablename__ = "stock_ledger"

    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("material.id"), nullable=False)
    storage_location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("location.id"), nullable=False
    )
    signed_quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    signed_value: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    material_document_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("material_document_item.id"), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StockBalance(Base, UUIDMixin):
    """Derived running total — always updated in the same transaction as the StockLedger
    append that produced it, never independently. One row per material+location."""

    __tablename__ = "stock_balance"
    __table_args__ = (UniqueConstraint("material_id", "storage_location_id", name="uq_stock_balance_dimension"),)

    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("material.id"), nullable=False)
    storage_location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("location.id"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    value: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)


class Reservation(Base, UUIDMixin, AuditMixin):
    """FR-018: dated availability reservation. Goods Issue only ever consumes stock through
    a Reservation in this build — matches "issue only from unrestricted stock" without a
    separate special/blocked stock-type model (the single StockBalance dimension per
    material+location *is* unrestricted stock here)."""

    __tablename__ = "reservation"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=False)
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("material.id"), nullable=False)
    storage_location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("location.id"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    issued_quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    purpose: Mapped[str | None] = mapped_column(String(300))
    # AIMS-specific integration point beyond the SAP MM spec: a maintenance order can
    # reserve/issue the parts it needs, same pattern as PurchaseRequisition.maintenance_order_id.
    maintenance_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("maintenance_order.id")
    )
    required_date: Mapped[date | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Open")  # Open|Fulfilled|Cancelled


class StockTransfer(Base, UUIDMixin, AuditMixin):
    """FR-019. One-step (301) posts a single document with both the issuing and receiving
    item and completes immediately. Two-step (303 issue / 305 receipt) splits into two
    documents with the material held "in transit" between them — represented here by
    status=InTransit rather than a separate transit-balance table, since the transit
    quantity is always fully derivable as sum(quantity) where status=InTransit. Reversal of
    a transfer (304/306) is out of scope for this stage."""

    __tablename__ = "stock_transfer"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=False)
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("material.id"), nullable=False)
    source_location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("location.id"), nullable=False)
    destination_location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("location.id"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    transfer_mode: Mapped[str] = mapped_column(String(10), nullable=False)  # OneStep|TwoStep
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # Completed|InTransit|Received|Cancelled
    issue_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("material_document.id")
    )
    receipt_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("material_document.id")
    )

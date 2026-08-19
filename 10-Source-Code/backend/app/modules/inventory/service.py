import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import write_audit_log
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.modules.inventory.models import (
    MaterialDocument,
    MaterialDocumentItem,
    Reservation,
    StockBalance,
    StockLedger,
    StockTransfer,
)
from app.modules.inventory.repository import (
    MaterialDocumentRepository,
    ReservationRepository,
    StockBalanceRepository,
    StockLedgerRepository,
    StockTransferRepository,
)
from app.modules.inventory.schemas import (
    GoodsIssueCreate,
    GoodsReceiptCreate,
    ReservationCreate,
    StockTransferIssueCreate,
    StockTransferOneStepCreate,
)
from app.modules.purchasing.models import Material, PurchaseOrder, PurchaseOrderItem

# Reversal movement pairs: original -> reversal. Only these two are reversible in this build.
_REVERSAL_MOVEMENT: dict[str, str] = {"101": "102", "201": "202"}


class MovementPostingService:
    """The single posting path every inventory movement goes through (ADR-0008's "one
    posting engine" principle) — Goods Receipt today, Goods Issue/Transfer in the next
    stage reuse the same StockLedger-append + StockBalance-update pattern, not duplicate
    posting logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.documents = MaterialDocumentRepository(db)
        self.balances = StockBalanceRepository(db)
        self.ledger = StockLedgerRepository(db)
        self.reservations = ReservationRepository(db)
        self.transfers_repo = StockTransferRepository(db)

    async def _get_po_item(self, po_item_id: uuid.UUID) -> PurchaseOrderItem:
        item = (
            await self.db.execute(select(PurchaseOrderItem).where(PurchaseOrderItem.id == po_item_id))
        ).scalar_one_or_none()
        if not item:
            raise NotFoundError(f"Purchase order item {po_item_id} not found")
        return item

    async def _adjust_balance(
        self, material_id: uuid.UUID, storage_location_id: uuid.UUID, delta_qty: float, delta_value: float
    ) -> StockBalance:
        balance = await self.balances.get_for_dimension(material_id, storage_location_id)
        if not balance:
            balance = StockBalance(material_id=material_id, storage_location_id=storage_location_id, quantity=0, value=0)
            self.balances.add(balance)
            await self.db.flush()
        balance.quantity = float(balance.quantity) + delta_qty
        balance.value = float(balance.value) + delta_value
        return balance

    async def _post_single_item_document(
        self, org_id: uuid.UUID, movement_type: str, reference_type: str | None, reference_id: uuid.UUID | None,
        material_id: uuid.UUID, storage_location_id: uuid.UUID, quantity: float, unit_price: float,
        actor_id: str | None,
    ) -> MaterialDocument:
        """Shared by Goods Issue and each leg of a transfer — one document, one item, one
        ledger append, one balance adjustment. Goods Receipt and reversal stay separate
        above/below since they carry extra field-specific bookkeeping (PO open-quantity,
        moving-average price, reservation state)."""
        document = MaterialDocument(
            org_id=org_id, movement_type=movement_type, posted_date=date.today(),
            reference_type=reference_type, reference_id=reference_id,
            created_by=uuid.UUID(actor_id) if actor_id else None,
        )
        self.documents.add(document)
        await self.db.flush()

        doc_item = MaterialDocumentItem(
            material_document_id=document.id, line_no=1, material_id=material_id,
            storage_location_id=storage_location_id, quantity=quantity, unit_price=unit_price,
        )
        self.documents.add_item(doc_item)
        await self.db.flush()

        signed_value = quantity * unit_price
        self.ledger.add(
            StockLedger(
                material_id=material_id, storage_location_id=storage_location_id,
                signed_quantity=quantity, signed_value=signed_value,
                material_document_item_id=doc_item.id, occurred_at=datetime.now(timezone.utc),
            )
        )
        await self._adjust_balance(material_id, storage_location_id, quantity, signed_value)
        return document

    async def _update_moving_average_price(self, material_id: uuid.UUID, received_qty: float, received_price: float) -> None:
        material = (await self.db.execute(select(Material).where(Material.id == material_id))).scalar_one()
        existing_balances = await self.balances.list_all(material_id)
        old_total_qty = sum(float(b.quantity) for b in existing_balances)
        old_avg_price = float(material.moving_average_price) if material.moving_average_price is not None else 0.0

        new_total_qty = old_total_qty + received_qty
        if new_total_qty > 0:
            material.moving_average_price = round(
                ((old_total_qty * old_avg_price) + (received_qty * received_price)) / new_total_qty, 2
            )

    async def post_goods_receipt(
        self, payload: GoodsReceiptCreate, org_id: uuid.UUID, actor_id: str | None
    ) -> MaterialDocument:
        po_item = await self._get_po_item(payload.po_item_id)
        po = (
            await self.db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_item.purchase_order_id))
        ).scalar_one()

        if po.status != "Sent":
            raise BusinessRuleError(
                f"Cannot post a goods receipt against a purchase order in status {po.status}",
                details=[{"field": "po_item_id", "issue": "po_not_sent"}],
            )

        open_quantity = float(po_item.quantity) - float(po_item.received_quantity)
        if payload.quantity > open_quantity:
            raise BusinessRuleError(
                f"Quantity {payload.quantity} exceeds open quantity {open_quantity}",
                details=[{"field": "quantity", "issue": "exceeds_open_quantity"}],
            )

        document = MaterialDocument(
            org_id=org_id, movement_type="101", posted_date=date.today(),
            reference_type="PurchaseOrder", reference_id=po.id,
            created_by=uuid.UUID(actor_id) if actor_id else None,
        )
        self.documents.add(document)
        await self.db.flush()

        unit_price = float(po_item.unit_price)
        doc_item = MaterialDocumentItem(
            material_document_id=document.id, line_no=1, material_id=po_item.material_id,
            storage_location_id=payload.storage_location_id, quantity=payload.quantity,
            unit_price=unit_price, po_item_id=po_item.id,
        )
        self.documents.add_item(doc_item)
        await self.db.flush()

        await self._update_moving_average_price(po_item.material_id, payload.quantity, unit_price)

        signed_value = payload.quantity * unit_price
        self.ledger.add(
            StockLedger(
                material_id=po_item.material_id, storage_location_id=payload.storage_location_id,
                signed_quantity=payload.quantity, signed_value=signed_value,
                material_document_item_id=doc_item.id, occurred_at=datetime.now(timezone.utc),
            )
        )

        await self._adjust_balance(po_item.material_id, payload.storage_location_id, payload.quantity, signed_value)

        po_item.received_quantity = float(po_item.received_quantity) + payload.quantity

        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="MaterialDocument",
            entity_id=document.id,
            new_value={"movement_type": "101", "material_id": str(po_item.material_id), "quantity": payload.quantity},
        )
        await self.db.commit()
        return await self.documents.get_by_id(document.id)

    async def post_goods_issue(
        self, payload: GoodsIssueCreate, org_id: uuid.UUID, actor_id: str | None
    ) -> MaterialDocument:
        """FR-018: issue only from unrestricted stock, against a dated reservation. Movement
        201; the single StockBalance dimension per material+location is this build's
        unrestricted stock (no separate special/blocked stock types)."""
        reservation = await self.reservations.get_by_id(payload.reservation_id)
        if not reservation:
            raise NotFoundError(f"Reservation {payload.reservation_id} not found")
        if reservation.status != "Open":
            raise BusinessRuleError(
                f"Cannot issue against a reservation in status {reservation.status}",
                details=[{"field": "reservation_id", "issue": "reservation_not_open"}],
            )

        open_reservation_qty = float(reservation.quantity) - float(reservation.issued_quantity)
        if payload.quantity > open_reservation_qty:
            raise BusinessRuleError(
                f"Quantity {payload.quantity} exceeds the reservation's open quantity {open_reservation_qty}",
                details=[{"field": "quantity", "issue": "exceeds_reservation_open_quantity"}],
            )

        balance = await self.balances.get_for_dimension(reservation.material_id, reservation.storage_location_id)
        available = float(balance.quantity) if balance else 0.0
        if payload.quantity > available:
            raise BusinessRuleError(
                f"Quantity {payload.quantity} exceeds available unrestricted stock {available}",
                details=[{"field": "quantity", "issue": "insufficient_stock"}],
            )

        unit_price = float(balance.value) / available if available > 0 else 0.0
        document = await self._post_single_item_document(
            org_id=org_id, movement_type="201", reference_type="Reservation", reference_id=reservation.id,
            material_id=reservation.material_id, storage_location_id=reservation.storage_location_id,
            quantity=-payload.quantity, unit_price=unit_price, actor_id=actor_id,
        )

        reservation.issued_quantity = float(reservation.issued_quantity) + payload.quantity
        if reservation.issued_quantity >= float(reservation.quantity):
            reservation.status = "Fulfilled"

        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="MaterialDocument",
            entity_id=document.id,
            new_value={"movement_type": "201", "material_id": str(reservation.material_id), "quantity": payload.quantity},
        )
        await self.db.commit()
        return await self.documents.get_by_id(document.id)

    async def post_one_step_transfer(
        self, payload: StockTransferOneStepCreate, org_id: uuid.UUID, actor_id: str | None
    ) -> StockTransfer:
        """FR-019 movement 301: a single document with both the issuing and receiving item,
        completes immediately (no transit state)."""
        source_balance = await self.balances.get_for_dimension(payload.material_id, payload.source_location_id)
        available = float(source_balance.quantity) if source_balance else 0.0
        if payload.quantity > available:
            raise BusinessRuleError(
                f"Quantity {payload.quantity} exceeds available stock {available} at the source location",
                details=[{"field": "quantity", "issue": "insufficient_stock"}],
            )
        unit_price = float(source_balance.value) / available if available > 0 else 0.0

        document = MaterialDocument(
            org_id=org_id, movement_type="301", posted_date=date.today(),
            reference_type=None, reference_id=None, created_by=uuid.UUID(actor_id) if actor_id else None,
        )
        self.documents.add(document)
        await self.db.flush()

        for line_no, (location_id, signed_qty) in enumerate(
            [(payload.source_location_id, -payload.quantity), (payload.destination_location_id, payload.quantity)],
            start=1,
        ):
            item = MaterialDocumentItem(
                material_document_id=document.id, line_no=line_no, material_id=payload.material_id,
                storage_location_id=location_id, quantity=signed_qty, unit_price=unit_price,
            )
            self.documents.add_item(item)
            await self.db.flush()
            self.ledger.add(
                StockLedger(
                    material_id=payload.material_id, storage_location_id=location_id,
                    signed_quantity=signed_qty, signed_value=signed_qty * unit_price,
                    material_document_item_id=item.id, occurred_at=datetime.now(timezone.utc),
                )
            )
            await self._adjust_balance(payload.material_id, location_id, signed_qty, signed_qty * unit_price)

        transfer = StockTransfer(
            org_id=org_id, material_id=payload.material_id, source_location_id=payload.source_location_id,
            destination_location_id=payload.destination_location_id, quantity=payload.quantity,
            transfer_mode="OneStep", status="Completed", issue_document_id=document.id,
            receipt_document_id=document.id,
        )
        self.transfers_repo.add(transfer)

        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="StockTransfer",
            entity_id=transfer.id if transfer.id else document.id,
            new_value={"movement_type": "301", "material_id": str(payload.material_id), "quantity": payload.quantity},
        )
        await self.db.commit()
        return transfer

    async def post_transfer_issue(
        self, payload: StockTransferIssueCreate, org_id: uuid.UUID, actor_id: str | None
    ) -> StockTransfer:
        """FR-019 movement 303: step one of a two-step transfer — issues from source only,
        leaving the material "in transit" (status=InTransit) until post_transfer_receipt."""
        source_balance = await self.balances.get_for_dimension(payload.material_id, payload.source_location_id)
        available = float(source_balance.quantity) if source_balance else 0.0
        if payload.quantity > available:
            raise BusinessRuleError(
                f"Quantity {payload.quantity} exceeds available stock {available} at the source location",
                details=[{"field": "quantity", "issue": "insufficient_stock"}],
            )
        unit_price = float(source_balance.value) / available if available > 0 else 0.0

        document = await self._post_single_item_document(
            org_id=org_id, movement_type="303", reference_type=None, reference_id=None,
            material_id=payload.material_id, storage_location_id=payload.source_location_id,
            quantity=-payload.quantity, unit_price=unit_price, actor_id=actor_id,
        )

        transfer = StockTransfer(
            org_id=org_id, material_id=payload.material_id, source_location_id=payload.source_location_id,
            destination_location_id=payload.destination_location_id, quantity=payload.quantity,
            transfer_mode="TwoStep", status="InTransit", issue_document_id=document.id,
        )
        self.transfers_repo.add(transfer)

        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="StockTransfer",
            entity_id=document.id,
            new_value={"movement_type": "303", "material_id": str(payload.material_id), "quantity": payload.quantity},
        )
        await self.db.commit()
        return await self.transfers_repo.get_by_id(transfer.id)

    async def post_transfer_receipt(self, transfer_id: uuid.UUID, actor_id: str | None) -> StockTransfer:
        """FR-019 movement 305: step two — receives the in-transit quantity at the
        destination, closing the transfer."""
        transfer = await self.transfers_repo.get_by_id(transfer_id)
        if not transfer:
            raise NotFoundError(f"Stock transfer {transfer_id} not found")
        if transfer.status != "InTransit":
            raise BusinessRuleError(
                f"Cannot receive a transfer in status {transfer.status}",
                details=[{"field": "status", "issue": "not_in_transit"}],
            )

        issue_document = await self.documents.get_by_id(transfer.issue_document_id)
        unit_price = float(issue_document.items[0].unit_price)

        document = await self._post_single_item_document(
            org_id=transfer.org_id, movement_type="305", reference_type=None, reference_id=None,
            material_id=transfer.material_id, storage_location_id=transfer.destination_location_id,
            quantity=float(transfer.quantity), unit_price=unit_price, actor_id=actor_id,
        )

        transfer.status = "Received"
        transfer.receipt_document_id = document.id

        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(transfer.org_id), action="Update", entity_type="StockTransfer",
            entity_id=transfer.id, new_value={"status": "Received"},
        )
        await self.db.commit()
        return await self.transfers_repo.get_by_id(transfer.id)

    async def reverse_document(self, document_id: uuid.UUID, actor_id: str | None) -> MaterialDocument:
        """Reverses a goods receipt (101->102) or a goods issue (201->202) — the two
        movement types this build allows reversal of (transfers are out of scope for this
        stage, see StockTransfer's docstring)."""
        original = await self.documents.get_by_id(document_id)
        if not original:
            raise NotFoundError(f"Material document {document_id} not found")
        reversal_movement_type = _REVERSAL_MOVEMENT.get(original.movement_type)
        if not reversal_movement_type:
            raise BusinessRuleError(
                "Only a goods receipt (101) or goods issue (201) can be reversed",
                details=[{"field": "movement_type", "issue": "not_reversible"}],
            )

        existing_reversal = await self.documents.get_reversal_of(document_id)
        if existing_reversal:
            raise BusinessRuleError(
                "This document has already been reversed",
                details=[{"field": "document_id", "issue": "already_reversed"}],
            )

        reversal = MaterialDocument(
            org_id=original.org_id, movement_type=reversal_movement_type, posted_date=date.today(),
            reference_type=original.reference_type, reference_id=original.reference_id,
            reversal_of_id=original.id, created_by=uuid.UUID(actor_id) if actor_id else None,
        )
        self.documents.add(reversal)
        await self.db.flush()

        for orig_item in original.items:
            reversed_qty = -float(orig_item.quantity)
            unit_price = float(orig_item.unit_price)
            reversal_item = MaterialDocumentItem(
                material_document_id=reversal.id, line_no=orig_item.line_no, material_id=orig_item.material_id,
                storage_location_id=orig_item.storage_location_id, quantity=reversed_qty,
                unit_price=unit_price, po_item_id=orig_item.po_item_id,
            )
            self.documents.add_item(reversal_item)
            await self.db.flush()

            self.ledger.add(
                StockLedger(
                    material_id=orig_item.material_id, storage_location_id=orig_item.storage_location_id,
                    signed_quantity=reversed_qty, signed_value=reversed_qty * unit_price,
                    material_document_item_id=reversal_item.id, occurred_at=datetime.now(timezone.utc),
                )
            )
            await self._adjust_balance(
                orig_item.material_id, orig_item.storage_location_id, reversed_qty, reversed_qty * unit_price
            )

            if orig_item.po_item_id:
                po_item = await self._get_po_item(orig_item.po_item_id)
                po_item.received_quantity = float(po_item.received_quantity) - float(orig_item.quantity)

        if original.reference_type == "Reservation" and original.reference_id:
            reservation = await self.reservations.get_by_id(original.reference_id)
            if reservation:
                reservation.issued_quantity = max(
                    0.0, float(reservation.issued_quantity) - abs(float(original.items[0].quantity))
                )
                if reservation.status == "Fulfilled":
                    reservation.status = "Open"

        # Moving-average price is deliberately not unwound on reversal — recomputing an
        # accurate historical average after other receipts may have already blended in is
        # ambiguous even in real SAP; treated as an accepted simplification for this build.

        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(original.org_id), action="Create", entity_type="MaterialDocument",
            entity_id=reversal.id, new_value={"movement_type": reversal_movement_type, "reversal_of_id": str(original.id)},
        )
        await self.db.commit()
        return await self.documents.get_by_id(reversal.id)

    async def get_document(self, document_id: uuid.UUID) -> MaterialDocument:
        document = await self.documents.get_by_id(document_id)
        if not document:
            raise NotFoundError(f"Material document {document_id} not found")
        return document

    async def list_documents_for_po(self, po_id: uuid.UUID) -> list[MaterialDocument]:
        return await self.documents.list_by_reference("PurchaseOrder", po_id)


class StockOverviewService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.balances = StockBalanceRepository(db)

    async def list_balances(self, material_id: uuid.UUID | None = None) -> list[StockBalance]:
        return await self.balances.list_all(material_id)


class ReservationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ReservationRepository(db)

    async def list_reservations(self, org_id: uuid.UUID, status: str | None = None) -> list[Reservation]:
        return await self.repo.list_all(org_id, status)

    async def get_reservation(self, reservation_id: uuid.UUID) -> Reservation:
        reservation = await self.repo.get_by_id(reservation_id)
        if not reservation:
            raise NotFoundError(f"Reservation {reservation_id} not found")
        return reservation

    async def create_reservation(
        self, payload: ReservationCreate, org_id: uuid.UUID, actor_id: str | None
    ) -> Reservation:
        reservation = Reservation(org_id=org_id, status="Open", **payload.model_dump())
        self.repo.add(reservation)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="Reservation",
            entity_id=reservation.id, new_value={"material_id": str(reservation.material_id), "quantity": payload.quantity},
        )
        await self.db.commit()
        return reservation

    async def cancel_reservation(self, reservation_id: uuid.UUID, actor_id: str | None) -> Reservation:
        reservation = await self.get_reservation(reservation_id)
        if float(reservation.issued_quantity) > 0:
            raise BusinessRuleError(
                "Cannot cancel a reservation that already has issued quantity",
                details=[{"field": "reservation_id", "issue": "has_issued_quantity"}],
            )
        reservation.status = "Cancelled"
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(reservation.org_id), action="Update", entity_type="Reservation",
            entity_id=reservation.id, new_value={"status": "Cancelled"},
        )
        await self.db.commit()
        return reservation


class StockTransferService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = StockTransferRepository(db)

    async def list_transfers(self, org_id: uuid.UUID, status: str | None = None) -> list[StockTransfer]:
        return await self.repo.list_all(org_id, status)

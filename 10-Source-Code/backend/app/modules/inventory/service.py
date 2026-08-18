import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import write_audit_log
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.modules.inventory.models import MaterialDocument, MaterialDocumentItem, StockBalance, StockLedger
from app.modules.inventory.repository import (
    MaterialDocumentRepository,
    StockBalanceRepository,
    StockLedgerRepository,
)
from app.modules.inventory.schemas import GoodsReceiptCreate
from app.modules.purchasing.models import Material, PurchaseOrder, PurchaseOrderItem


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

    async def _get_po_item(self, po_item_id: uuid.UUID) -> PurchaseOrderItem:
        item = (
            await self.db.execute(select(PurchaseOrderItem).where(PurchaseOrderItem.id == po_item_id))
        ).scalar_one_or_none()
        if not item:
            raise NotFoundError(f"Purchase order item {po_item_id} not found")
        return item

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

        balance = await self.balances.get_for_dimension(po_item.material_id, payload.storage_location_id)
        if not balance:
            balance = StockBalance(
                material_id=po_item.material_id, storage_location_id=payload.storage_location_id,
                quantity=0, value=0,
            )
            self.balances.add(balance)
            await self.db.flush()
        balance.quantity = float(balance.quantity) + payload.quantity
        balance.value = float(balance.value) + signed_value

        po_item.received_quantity = float(po_item.received_quantity) + payload.quantity

        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="MaterialDocument",
            entity_id=document.id,
            new_value={"movement_type": "101", "material_id": str(po_item.material_id), "quantity": payload.quantity},
        )
        await self.db.commit()
        return await self.documents.get_by_id(document.id)

    async def reverse_goods_receipt(self, document_id: uuid.UUID, actor_id: str | None) -> MaterialDocument:
        original = await self.documents.get_by_id(document_id)
        if not original:
            raise NotFoundError(f"Material document {document_id} not found")
        if original.movement_type != "101":
            raise BusinessRuleError(
                "Only a goods receipt (movement 101) can be reversed",
                details=[{"field": "movement_type", "issue": "not_reversible"}],
            )

        existing_reversal = await self.documents.get_reversal_of(document_id)
        if existing_reversal:
            raise BusinessRuleError(
                "This goods receipt has already been reversed",
                details=[{"field": "document_id", "issue": "already_reversed"}],
            )

        reversal = MaterialDocument(
            org_id=original.org_id, movement_type="102", posted_date=date.today(),
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

            balance = await self.balances.get_for_dimension(orig_item.material_id, orig_item.storage_location_id)
            if balance:
                balance.quantity = float(balance.quantity) + reversed_qty
                balance.value = float(balance.value) + (reversed_qty * unit_price)

            if orig_item.po_item_id:
                po_item = await self._get_po_item(orig_item.po_item_id)
                po_item.received_quantity = float(po_item.received_quantity) - float(orig_item.quantity)

        # Moving-average price is deliberately not unwound on reversal — recomputing an
        # accurate historical average after other receipts may have already blended in is
        # ambiguous even in real SAP; treated as an accepted simplification for this build.

        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(original.org_id), action="Create", entity_type="MaterialDocument",
            entity_id=reversal.id, new_value={"movement_type": "102", "reversal_of_id": str(original.id)},
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

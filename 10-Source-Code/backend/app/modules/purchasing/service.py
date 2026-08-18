import uuid
from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import write_audit_log
from app.core.exceptions import BusinessRuleError, ConflictError, ForbiddenError, NotFoundError
from app.modules.purchasing.models import (
    Material,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    PurchaseRequisitionItem,
    PurchasingInfoRecord,
    Quotation,
    QuotationItem,
    QuotaArrangement,
    RFQ,
    RFQSupplierInvite,
    SourceListEntry,
    Supplier,
)
from app.modules.purchasing.repository import (
    MaterialRepository,
    PurchaseOrderRepository,
    PurchaseRequisitionRepository,
    PurchasingInfoRecordRepository,
    QuotaArrangementRepository,
    QuotationRepository,
    RFQRepository,
    RFQSupplierInviteRepository,
    SourceListEntryRepository,
    SupplierRepository,
)
from app.modules.purchasing.schemas import (
    MaterialCreate,
    PurchaseRequisitionCreate,
    PurchasingInfoRecordCreate,
    QuotaArrangementCreate,
    QuotationCreate,
    RFQCreate,
    SourceListEntryCreate,
    SupplierBlockUpdate,
    SupplierCreate,
)
from app.modules.purchasing.source_engine import (
    InfoRecordInput,
    QuotaInput,
    SourceCandidate,
    SourceListInput,
    determine_sources,
)


class MaterialService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MaterialRepository(db)

    async def list_materials(self, org_id: uuid.UUID) -> list[Material]:
        return await self.repo.list_all(org_id)

    async def get_material(self, material_id: uuid.UUID) -> Material:
        material = await self.repo.get_by_id(material_id)
        if not material:
            raise NotFoundError(f"Material {material_id} not found")
        return material

    async def create_material(self, payload: MaterialCreate, org_id: uuid.UUID, actor_id: str | None) -> Material:
        existing = await self.repo.get_by_number(org_id, payload.material_number)
        if existing:
            raise ConflictError(f"Material number '{payload.material_number}' already exists")

        material = Material(org_id=org_id, **payload.model_dump())
        self.repo.add(material)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="Material",
            entity_id=material.id, new_value={"material_number": material.material_number, "name": material.name},
        )
        await self.db.commit()
        return material


class SupplierService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SupplierRepository(db)

    async def list_suppliers(self, org_id: uuid.UUID) -> list[Supplier]:
        return await self.repo.list_all(org_id)

    async def get_supplier(self, supplier_id: uuid.UUID) -> Supplier:
        supplier = await self.repo.get_by_id(supplier_id)
        if not supplier:
            raise NotFoundError(f"Supplier {supplier_id} not found")
        return supplier

    async def create_supplier(self, payload: SupplierCreate, org_id: uuid.UUID, actor_id: str | None) -> Supplier:
        existing = await self.repo.get_by_number(org_id, payload.supplier_number)
        if existing:
            raise ConflictError(f"Supplier number '{payload.supplier_number}' already exists")

        supplier = Supplier(org_id=org_id, **payload.model_dump())
        self.repo.add(supplier)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="Supplier",
            entity_id=supplier.id, new_value={"supplier_number": supplier.supplier_number, "name": supplier.name},
        )
        await self.db.commit()
        return supplier

    async def update_block(
        self, supplier_id: uuid.UUID, payload: SupplierBlockUpdate, actor_id: str | None
    ) -> Supplier:
        supplier = await self.get_supplier(supplier_id)
        supplier.is_blocked = payload.is_blocked
        supplier.block_reason = payload.block_reason if payload.is_blocked else None
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(supplier.org_id), action="Update", entity_type="Supplier",
            entity_id=supplier.id, new_value={"is_blocked": supplier.is_blocked, "block_reason": supplier.block_reason},
        )
        await self.db.commit()
        return supplier


class PurchasingInfoRecordService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PurchasingInfoRecordRepository(db)

    async def list_for_material(self, org_id: uuid.UUID, material_id: uuid.UUID) -> list[PurchasingInfoRecord]:
        return await self.repo.list_by_material(org_id, material_id)

    async def create(
        self, payload: PurchasingInfoRecordCreate, org_id: uuid.UUID, actor_id: str | None
    ) -> PurchasingInfoRecord:
        record = PurchasingInfoRecord(org_id=org_id, **payload.model_dump())
        self.repo.add(record)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="PurchasingInfoRecord",
            entity_id=record.id, new_value={"material_id": str(record.material_id), "price": float(record.price)},
        )
        await self.db.commit()
        return record


class SourceListEntryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SourceListEntryRepository(db)

    async def list_for_material(self, org_id: uuid.UUID, material_id: uuid.UUID) -> list[SourceListEntry]:
        return await self.repo.list_by_material(org_id, material_id)

    async def create(self, payload: SourceListEntryCreate, org_id: uuid.UUID, actor_id: str | None) -> SourceListEntry:
        entry = SourceListEntry(org_id=org_id, **payload.model_dump())
        self.repo.add(entry)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="SourceListEntry",
            entity_id=entry.id, new_value={"material_id": str(entry.material_id), "is_fixed": entry.is_fixed},
        )
        await self.db.commit()
        return entry


class QuotaArrangementService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = QuotaArrangementRepository(db)

    async def list_for_material(self, org_id: uuid.UUID, material_id: uuid.UUID) -> list[QuotaArrangement]:
        return await self.repo.list_by_material(org_id, material_id)

    async def create(
        self, payload: QuotaArrangementCreate, org_id: uuid.UUID, actor_id: str | None
    ) -> QuotaArrangement:
        arrangement = QuotaArrangement(org_id=org_id, **payload.model_dump())
        self.repo.add(arrangement)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="QuotaArrangement",
            entity_id=arrangement.id,
            new_value={"material_id": str(arrangement.material_id), "quota_percentage": float(arrangement.quota_percentage)},
        )
        await self.db.commit()
        return arrangement


class SourceDeterminationService:
    """Orchestration layer: loads the relevant rows for a material and hands them to the pure
    `determine_sources` engine (source_engine.py) — no business logic lives here, only I/O."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.source_lists = SourceListEntryRepository(db)
        self.quotas = QuotaArrangementRepository(db)
        self.info_records = PurchasingInfoRecordRepository(db)
        self.suppliers = SupplierRepository(db)

    async def determine(self, org_id: uuid.UUID, material_id: uuid.UUID, as_of: date) -> list[SourceCandidate]:
        source_list_rows = await self.source_lists.list_by_material(org_id, material_id)
        quota_rows = await self.quotas.list_by_material(org_id, material_id)
        info_record_rows = await self.info_records.list_by_material(org_id, material_id)
        all_suppliers = await self.suppliers.list_all(org_id)
        blocked_ids = {s.id for s in all_suppliers if s.is_blocked}

        return determine_sources(
            source_list=[
                SourceListInput(e.supplier_id, e.is_fixed, e.is_blocked, e.valid_from, e.valid_to)
                for e in source_list_rows
            ],
            quotas=[
                QuotaInput(q.supplier_id, float(q.quota_percentage), q.valid_from, q.valid_to) for q in quota_rows
            ],
            info_records=[
                InfoRecordInput(r.supplier_id, float(r.price), r.valid_from, r.valid_to) for r in info_record_rows
            ],
            blocked_supplier_ids=blocked_ids,
            as_of=as_of,
        )


# FR-006/FR-007, single-step release matching AIMS's existing Defect/Risk/Asset approve
# pattern (see defect/service.py's _VALID_TRANSITIONS) — not a configurable multi-step
# delegation/escalation workflow engine. "Converted" is reserved for the RFQ/PO stage.
_PR_VALID_TRANSITIONS: dict[str, set[str]] = {
    "Draft": {"Submitted", "Withdrawn"},
    "Submitted": {"Approved", "Rejected", "Withdrawn"},
    "Approved": set(),
    "Rejected": set(),
    "Withdrawn": set(),
}


class PurchaseRequisitionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PurchaseRequisitionRepository(db)

    async def list_requisitions(
        self, org_id: uuid.UUID, status: str | None, page: int, page_size: int
    ) -> tuple[list[PurchaseRequisition], int]:
        return await self.repo.list_all(org_id, status, (page - 1) * page_size, page_size)

    async def get_requisition(self, requisition_id: uuid.UUID) -> PurchaseRequisition:
        requisition = await self.repo.get_by_id(requisition_id)
        if not requisition:
            raise NotFoundError(f"Purchase requisition {requisition_id} not found")
        return requisition

    async def create_requisition(
        self, payload: PurchaseRequisitionCreate, org_id: uuid.UUID, requester_id: str
    ) -> PurchaseRequisition:
        requisition = PurchaseRequisition(
            org_id=org_id,
            requester_id=uuid.UUID(requester_id),
            status="Draft",
            requested_date=payload.requested_date,
            required_date=payload.required_date,
            maintenance_order_id=payload.maintenance_order_id,
            defect_id=payload.defect_id,
        )
        self.repo.add(requisition)
        await self.db.flush()

        for line_no, item in enumerate(payload.items, start=1):
            self.repo.add_item(
                PurchaseRequisitionItem(
                    purchase_requisition_id=requisition.id,
                    line_no=line_no,
                    material_id=item.material_id,
                    quantity=item.quantity,
                    estimated_price=item.estimated_price,
                    required_date=item.required_date,
                )
            )

        await write_audit_log(
            self.db, user_id=requester_id, org_id=str(org_id), action="Create", entity_type="PurchaseRequisition",
            entity_id=requisition.id, new_value={"item_count": len(payload.items)},
        )
        await self.db.commit()
        return await self.get_requisition(requisition.id)

    async def _transition(
        self, requisition_id: uuid.UUID, target_status: str, actor_id: str, reason: str | None = None
    ) -> PurchaseRequisition:
        requisition = await self.get_requisition(requisition_id)
        allowed = _PR_VALID_TRANSITIONS.get(requisition.status, set())
        if target_status not in allowed:
            raise BusinessRuleError(
                f"Invalid transition: {requisition.status} -> {target_status}",
                details=[{"field": "status", "issue": "invalid_transition"}],
            )

        requisition.status = target_status
        if target_status in {"Approved", "Rejected"}:
            requisition.decision_by = uuid.UUID(actor_id)
            requisition.decision_at = datetime.now(timezone.utc)
            requisition.decision_reason = reason

        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(requisition.org_id), action="Update",
            entity_type="PurchaseRequisition", entity_id=requisition.id, new_value={"status": target_status},
        )
        await self.db.commit()
        return await self.get_requisition(requisition.id)

    async def submit(self, requisition_id: uuid.UUID, actor_id: str) -> PurchaseRequisition:
        return await self._transition(requisition_id, "Submitted", actor_id)

    async def approve(self, requisition_id: uuid.UUID, actor_id: str) -> PurchaseRequisition:
        requisition = await self.get_requisition(requisition_id)
        if str(requisition.requester_id) == actor_id:
            raise ForbiddenError("A requester cannot approve their own purchase requisition")
        return await self._transition(requisition_id, "Approved", actor_id)

    async def reject(self, requisition_id: uuid.UUID, actor_id: str, reason: str | None) -> PurchaseRequisition:
        return await self._transition(requisition_id, "Rejected", actor_id, reason)

    async def withdraw(self, requisition_id: uuid.UUID, actor_id: str) -> PurchaseRequisition:
        requisition = await self.get_requisition(requisition_id)
        if str(requisition.requester_id) != actor_id:
            raise ForbiddenError("Only the requester can withdraw a purchase requisition")
        return await self._transition(requisition_id, "Withdrawn", actor_id)


class RFQService:
    """FR-008: released PR-to-RFQ lineage. Dispatch is symbolic (no real email/PDF output)."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RFQRepository(db)
        self.invites = RFQSupplierInviteRepository(db)
        self.requisitions = PurchaseRequisitionRepository(db)

    async def list_rfqs(self, org_id: uuid.UUID) -> list[RFQ]:
        return await self.repo.list_all(org_id)

    async def get_rfq(self, rfq_id: uuid.UUID) -> RFQ:
        rfq = await self.repo.get_by_id(rfq_id)
        if not rfq:
            raise NotFoundError(f"RFQ {rfq_id} not found")
        return rfq

    async def create_rfq(self, payload: RFQCreate, org_id: uuid.UUID, actor_id: str | None) -> RFQ:
        requisition = await self.requisitions.get_by_id(payload.purchase_requisition_id)
        if not requisition:
            raise NotFoundError(f"Purchase requisition {payload.purchase_requisition_id} not found")
        if requisition.status != "Approved":
            raise BusinessRuleError(
                "Only an Approved purchase requisition can be sourced through an RFQ",
                details=[{"field": "purchase_requisition_id", "issue": "not_approved"}],
            )

        rfq = RFQ(
            org_id=org_id, purchase_requisition_id=payload.purchase_requisition_id,
            status="Draft", deadline=payload.deadline,
        )
        self.repo.add(rfq)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="RFQ",
            entity_id=rfq.id, new_value={"purchase_requisition_id": str(requisition.id)},
        )
        await self.db.commit()
        return rfq

    async def invite_supplier(self, rfq_id: uuid.UUID, supplier_id: uuid.UUID, actor_id: str | None) -> RFQSupplierInvite:
        await self.get_rfq(rfq_id)
        invite = RFQSupplierInvite(rfq_id=rfq_id, supplier_id=supplier_id)
        self.invites.add(invite)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=None, action="Create", entity_type="RFQSupplierInvite",
            entity_id=invite.id, new_value={"rfq_id": str(rfq_id), "supplier_id": str(supplier_id)},
        )
        await self.db.commit()
        return invite

    async def list_invites(self, rfq_id: uuid.UUID) -> list[RFQSupplierInvite]:
        return await self.invites.list_by_rfq(rfq_id)

    async def dispatch(self, rfq_id: uuid.UUID, actor_id: str | None) -> RFQ:
        rfq = await self.get_rfq(rfq_id)
        if rfq.status != "Draft":
            raise BusinessRuleError(
                f"Cannot dispatch an RFQ in status {rfq.status}",
                details=[{"field": "status", "issue": "invalid_transition"}],
            )
        rfq.status = "Dispatched"
        now = datetime.now(timezone.utc)
        for invite in await self.invites.list_by_rfq(rfq_id):
            invite.dispatched_at = now

        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(rfq.org_id), action="Update", entity_type="RFQ",
            entity_id=rfq.id, new_value={"status": "Dispatched"},
        )
        await self.db.commit()
        return rfq


class QuotationService:
    """FR-008: buyer-recorded supplier bids and item-level award. Awarding an item
    automatically un-awards any other quotation item for the same PR line — a PR line can
    only be fulfilled by one supplier in this simplified model."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = QuotationRepository(db)
        self.rfqs = RFQRepository(db)

    async def list_for_rfq(self, rfq_id: uuid.UUID) -> list[Quotation]:
        return await self.repo.list_by_rfq(rfq_id)

    async def create_quotation(self, payload: QuotationCreate, org_id: uuid.UUID, actor_id: str | None) -> Quotation:
        rfq = await self.rfqs.get_by_id(payload.rfq_id)
        if not rfq:
            raise NotFoundError(f"RFQ {payload.rfq_id} not found")

        quotation = Quotation(
            org_id=org_id, rfq_id=payload.rfq_id, supplier_id=payload.supplier_id,
            submitted_date=payload.submitted_date,
        )
        self.repo.add(quotation)
        await self.db.flush()

        for item in payload.items:
            self.repo.add_item(
                QuotationItem(
                    quotation_id=quotation.id, pr_item_id=item.pr_item_id, material_id=item.material_id,
                    quantity=item.quantity, unit_price=item.unit_price,
                )
            )

        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="Quotation",
            entity_id=quotation.id, new_value={"rfq_id": str(payload.rfq_id), "supplier_id": str(payload.supplier_id)},
        )
        await self.db.commit()
        return await self.repo.get_by_id(quotation.id)

    async def award_item(self, item_id: uuid.UUID, actor_id: str | None) -> QuotationItem:
        item = await self.repo.get_item_by_id(item_id)
        if not item:
            raise NotFoundError(f"Quotation item {item_id} not found")

        existing_award = await self.repo.find_awarded_item_for_pr_item(item.pr_item_id)
        if existing_award and existing_award.id != item.id:
            existing_award.is_awarded = False

        item.is_awarded = True
        await write_audit_log(
            self.db, user_id=actor_id, org_id=None, action="Update", entity_type="QuotationItem",
            entity_id=item.id, new_value={"is_awarded": True},
        )
        await self.db.commit()
        return item


class PurchaseOrderService:
    """FR-010, single-step approval matching PurchaseRequisitionService's pattern. Supplier-
    split conversion: one PO per supplier from that RFQ's currently-awarded quotation items."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PurchaseOrderRepository(db)
        self.quotations = QuotationRepository(db)
        self.rfqs = RFQRepository(db)

    async def list_orders(
        self, org_id: uuid.UUID, status: str | None, page: int, page_size: int
    ) -> tuple[list[PurchaseOrder], int]:
        return await self.repo.list_all(org_id, status, (page - 1) * page_size, page_size)

    async def get_order(self, order_id: uuid.UUID) -> PurchaseOrder:
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise NotFoundError(f"Purchase order {order_id} not found")
        return order

    async def convert_from_rfq(self, rfq_id: uuid.UUID, org_id: uuid.UUID, actor_id: str | None) -> list[PurchaseOrder]:
        rfq = await self.rfqs.get_by_id(rfq_id)
        if not rfq:
            raise NotFoundError(f"RFQ {rfq_id} not found")

        awarded_items = await self.quotations.list_awarded_for_rfq(rfq_id)
        if not awarded_items:
            raise BusinessRuleError(
                "No awarded quotation items to convert",
                details=[{"field": "rfq_id", "issue": "nothing_awarded"}],
            )

        by_supplier: dict[uuid.UUID, list[QuotationItem]] = {}
        for item in awarded_items:
            quotation = await self.quotations.get_by_id(item.quotation_id)
            by_supplier.setdefault(quotation.supplier_id, []).append(item)

        created_orders: list[PurchaseOrder] = []
        for supplier_id, items in by_supplier.items():
            order = PurchaseOrder(
                org_id=org_id, supplier_id=supplier_id, purchase_requisition_id=rfq.purchase_requisition_id,
                rfq_id=rfq.id, status="Draft", order_date=date.today(),
                # AuditMixin.created_by has no auto-population hook anywhere in this codebase
                # (verified — nothing else sets it), so it must be set explicitly here for
                # approve()'s self-approval check below to have real data to compare against.
                created_by=uuid.UUID(actor_id) if actor_id else None,
            )
            self.repo.add(order)
            await self.db.flush()

            for line_no, item in enumerate(items, start=1):
                self.repo.add_item(
                    PurchaseOrderItem(
                        purchase_order_id=order.id, line_no=line_no, material_id=item.material_id,
                        quantity=item.quantity, unit_price=item.unit_price, pr_item_id=item.pr_item_id,
                    )
                )

            await write_audit_log(
                self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="PurchaseOrder",
                entity_id=order.id, new_value={"supplier_id": str(supplier_id), "item_count": len(items)},
            )
            created_orders.append(order)

        await self.db.commit()
        return [await self.repo.get_by_id(o.id) for o in created_orders]

    async def approve(self, order_id: uuid.UUID, actor_id: str) -> PurchaseOrder:
        order = await self.get_order(order_id)
        if str(order.created_by) == actor_id:
            raise ForbiddenError("The creator of a purchase order cannot approve it")
        if order.status != "Draft":
            raise BusinessRuleError(
                f"Cannot approve a purchase order in status {order.status}",
                details=[{"field": "status", "issue": "invalid_transition"}],
            )
        order.status = "Approved"
        order.approved_by = uuid.UUID(actor_id)
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(order.org_id), action="Update", entity_type="PurchaseOrder",
            entity_id=order.id, new_value={"status": "Approved"},
        )
        await self.db.commit()
        return order

    async def send(self, order_id: uuid.UUID, actor_id: str | None) -> PurchaseOrder:
        order = await self.get_order(order_id)
        if order.status != "Approved":
            raise BusinessRuleError(
                f"Cannot send a purchase order in status {order.status}",
                details=[{"field": "status", "issue": "invalid_transition"}],
            )
        order.status = "Sent"
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(order.org_id), action="Update", entity_type="PurchaseOrder",
            entity_id=order.id, new_value={"status": "Sent"},
        )
        await self.db.commit()
        return order

    async def confirm(self, order_id: uuid.UUID, confirmed_date: date, actor_id: str | None) -> PurchaseOrder:
        order = await self.get_order(order_id)
        if order.status != "Sent":
            raise BusinessRuleError(
                f"Cannot confirm a purchase order in status {order.status}",
                details=[{"field": "status", "issue": "invalid_transition"}],
            )
        order.confirmed_date = confirmed_date
        order.confirmed_by_supplier = True
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(order.org_id), action="Update", entity_type="PurchaseOrder",
            entity_id=order.id, new_value={"confirmed_date": str(confirmed_date)},
        )
        await self.db.commit()
        return order

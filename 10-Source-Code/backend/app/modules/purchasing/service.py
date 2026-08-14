import uuid
from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import write_audit_log
from app.core.exceptions import BusinessRuleError, ConflictError, ForbiddenError, NotFoundError
from app.modules.purchasing.models import (
    Material,
    PurchaseRequisition,
    PurchaseRequisitionItem,
    PurchasingInfoRecord,
    QuotaArrangement,
    SourceListEntry,
    Supplier,
)
from app.modules.purchasing.repository import (
    MaterialRepository,
    PurchaseRequisitionRepository,
    PurchasingInfoRecordRepository,
    QuotaArrangementRepository,
    SourceListEntryRepository,
    SupplierRepository,
)
from app.modules.purchasing.schemas import (
    MaterialCreate,
    PurchaseRequisitionCreate,
    PurchasingInfoRecordCreate,
    QuotaArrangementCreate,
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

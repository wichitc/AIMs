import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import write_audit_log
from app.core.exceptions import ConflictError, NotFoundError
from app.modules.purchasing.models import Material, PurchasingInfoRecord, QuotaArrangement, SourceListEntry, Supplier
from app.modules.purchasing.repository import (
    MaterialRepository,
    PurchasingInfoRecordRepository,
    QuotaArrangementRepository,
    SourceListEntryRepository,
    SupplierRepository,
)
from app.modules.purchasing.schemas import (
    MaterialCreate,
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

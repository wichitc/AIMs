import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.purchasing.models import (
    Material,
    PurchasingInfoRecord,
    QuotaArrangement,
    SourceListEntry,
    Supplier,
)


class MaterialRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self, org_id: uuid.UUID) -> list[Material]:
        stmt = select(Material).where(Material.org_id == org_id, Material.is_deleted.is_(False))
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_by_id(self, material_id: uuid.UUID) -> Material | None:
        stmt = select(Material).where(Material.id == material_id, Material.is_deleted.is_(False))
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_by_number(self, org_id: uuid.UUID, material_number: str) -> Material | None:
        stmt = select(Material).where(Material.org_id == org_id, Material.material_number == material_number)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def add(self, material: Material) -> None:
        self.db.add(material)


class SupplierRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self, org_id: uuid.UUID) -> list[Supplier]:
        stmt = select(Supplier).where(Supplier.org_id == org_id, Supplier.is_deleted.is_(False))
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_by_id(self, supplier_id: uuid.UUID) -> Supplier | None:
        stmt = select(Supplier).where(Supplier.id == supplier_id, Supplier.is_deleted.is_(False))
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_by_number(self, org_id: uuid.UUID, supplier_number: str) -> Supplier | None:
        stmt = select(Supplier).where(Supplier.org_id == org_id, Supplier.supplier_number == supplier_number)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def add(self, supplier: Supplier) -> None:
        self.db.add(supplier)


class PurchasingInfoRecordRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_material(self, org_id: uuid.UUID, material_id: uuid.UUID) -> list[PurchasingInfoRecord]:
        stmt = select(PurchasingInfoRecord).where(
            PurchasingInfoRecord.org_id == org_id, PurchasingInfoRecord.material_id == material_id
        )
        return list((await self.db.execute(stmt)).scalars().all())

    def add(self, record: PurchasingInfoRecord) -> None:
        self.db.add(record)


class SourceListEntryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_material(self, org_id: uuid.UUID, material_id: uuid.UUID) -> list[SourceListEntry]:
        stmt = select(SourceListEntry).where(
            SourceListEntry.org_id == org_id, SourceListEntry.material_id == material_id
        )
        return list((await self.db.execute(stmt)).scalars().all())

    def add(self, entry: SourceListEntry) -> None:
        self.db.add(entry)


class QuotaArrangementRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_material(self, org_id: uuid.UUID, material_id: uuid.UUID) -> list[QuotaArrangement]:
        stmt = select(QuotaArrangement).where(
            QuotaArrangement.org_id == org_id, QuotaArrangement.material_id == material_id
        )
        return list((await self.db.execute(stmt)).scalars().all())

    def add(self, arrangement: QuotaArrangement) -> None:
        self.db.add(arrangement)

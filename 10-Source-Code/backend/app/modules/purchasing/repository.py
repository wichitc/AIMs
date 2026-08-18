import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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


class PurchaseRequisitionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(
        self, org_id: uuid.UUID, status: str | None, offset: int, limit: int
    ) -> tuple[list[PurchaseRequisition], int]:
        stmt = select(PurchaseRequisition).where(PurchaseRequisition.org_id == org_id)
        if status:
            stmt = stmt.where(PurchaseRequisition.status == status)
        total = len((await self.db.execute(stmt)).scalars().all())
        stmt = stmt.offset(offset).limit(limit).options(selectinload(PurchaseRequisition.items))
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total

    async def get_by_id(self, requisition_id: uuid.UUID) -> PurchaseRequisition | None:
        stmt = (
            select(PurchaseRequisition)
            .where(PurchaseRequisition.id == requisition_id)
            .options(selectinload(PurchaseRequisition.items))
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def add(self, requisition: PurchaseRequisition) -> None:
        self.db.add(requisition)

    def add_item(self, item: PurchaseRequisitionItem) -> None:
        self.db.add(item)


class RFQRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self, org_id: uuid.UUID) -> list[RFQ]:
        stmt = select(RFQ).where(RFQ.org_id == org_id)
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_by_id(self, rfq_id: uuid.UUID) -> RFQ | None:
        return (await self.db.execute(select(RFQ).where(RFQ.id == rfq_id))).scalar_one_or_none()

    def add(self, rfq: RFQ) -> None:
        self.db.add(rfq)


class RFQSupplierInviteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_rfq(self, rfq_id: uuid.UUID) -> list[RFQSupplierInvite]:
        stmt = select(RFQSupplierInvite).where(RFQSupplierInvite.rfq_id == rfq_id)
        return list((await self.db.execute(stmt)).scalars().all())

    def add(self, invite: RFQSupplierInvite) -> None:
        self.db.add(invite)


class QuotationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_rfq(self, rfq_id: uuid.UUID) -> list[Quotation]:
        stmt = select(Quotation).where(Quotation.rfq_id == rfq_id).options(selectinload(Quotation.items))
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_by_id(self, quotation_id: uuid.UUID) -> Quotation | None:
        stmt = select(Quotation).where(Quotation.id == quotation_id).options(selectinload(Quotation.items))
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_item_by_id(self, item_id: uuid.UUID) -> QuotationItem | None:
        return (
            await self.db.execute(select(QuotationItem).where(QuotationItem.id == item_id))
        ).scalar_one_or_none()

    async def find_awarded_item_for_pr_item(self, pr_item_id: uuid.UUID) -> QuotationItem | None:
        stmt = select(QuotationItem).where(
            QuotationItem.pr_item_id == pr_item_id, QuotationItem.is_awarded.is_(True)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_awarded_for_rfq(self, rfq_id: uuid.UUID) -> list[QuotationItem]:
        stmt = (
            select(QuotationItem)
            .join(Quotation, Quotation.id == QuotationItem.quotation_id)
            .where(Quotation.rfq_id == rfq_id, QuotationItem.is_awarded.is_(True))
        )
        return list((await self.db.execute(stmt)).scalars().all())

    def add(self, quotation: Quotation) -> None:
        self.db.add(quotation)

    def add_item(self, item: QuotationItem) -> None:
        self.db.add(item)


class PurchaseOrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(
        self, org_id: uuid.UUID, status: str | None, offset: int, limit: int
    ) -> tuple[list[PurchaseOrder], int]:
        stmt = select(PurchaseOrder).where(PurchaseOrder.org_id == org_id)
        if status:
            stmt = stmt.where(PurchaseOrder.status == status)
        total = len((await self.db.execute(stmt)).scalars().all())
        stmt = stmt.offset(offset).limit(limit).options(selectinload(PurchaseOrder.items))
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total

    async def get_by_id(self, order_id: uuid.UUID) -> PurchaseOrder | None:
        stmt = select(PurchaseOrder).where(PurchaseOrder.id == order_id).options(selectinload(PurchaseOrder.items))
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def add(self, order: PurchaseOrder) -> None:
        self.db.add(order)

    def add_item(self, item: PurchaseOrderItem) -> None:
        self.db.add(item)

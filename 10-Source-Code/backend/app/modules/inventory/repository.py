import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.inventory.models import MaterialDocument, MaterialDocumentItem, StockBalance, StockLedger


class MaterialDocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, document_id: uuid.UUID) -> MaterialDocument | None:
        stmt = (
            select(MaterialDocument)
            .where(MaterialDocument.id == document_id)
            .options(selectinload(MaterialDocument.items))
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_by_reference(self, reference_type: str, reference_id: uuid.UUID) -> list[MaterialDocument]:
        stmt = (
            select(MaterialDocument)
            .where(MaterialDocument.reference_type == reference_type, MaterialDocument.reference_id == reference_id)
            .options(selectinload(MaterialDocument.items))
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_reversal_of(self, original_id: uuid.UUID) -> MaterialDocument | None:
        stmt = select(MaterialDocument).where(MaterialDocument.reversal_of_id == original_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def add(self, document: MaterialDocument) -> None:
        self.db.add(document)

    def add_item(self, item: MaterialDocumentItem) -> None:
        self.db.add(item)


class StockBalanceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self, material_id: uuid.UUID | None = None) -> list[StockBalance]:
        stmt = select(StockBalance)
        if material_id:
            stmt = stmt.where(StockBalance.material_id == material_id)
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_for_dimension(
        self, material_id: uuid.UUID, storage_location_id: uuid.UUID
    ) -> StockBalance | None:
        stmt = select(StockBalance).where(
            StockBalance.material_id == material_id, StockBalance.storage_location_id == storage_location_id
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def add(self, balance: StockBalance) -> None:
        self.db.add(balance)


class StockLedgerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def add(self, entry: StockLedger) -> None:
        self.db.add(entry)

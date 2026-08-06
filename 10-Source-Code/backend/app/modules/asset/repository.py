import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.asset.models import Asset, AssetClass, Criticality, Equipment, Location


class LocationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self, org_id: uuid.UUID) -> list[Location]:
        stmt = select(Location).where(Location.org_id == org_id)
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_by_id(self, location_id: uuid.UUID) -> Location | None:
        return (await self.db.execute(select(Location).where(Location.id == location_id))).scalar_one_or_none()

    def add(self, location: Location) -> None:
        self.db.add(location)


class AssetClassRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[AssetClass]:
        return list((await self.db.execute(select(AssetClass))).scalars().all())


class AssetRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_tag_number(self, tag_number: str) -> Asset | None:
        stmt = select(Asset).where(Asset.tag_number == tag_number, Asset.is_deleted.is_(False))
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, asset_id: uuid.UUID) -> Asset | None:
        stmt = select(Asset).where(Asset.id == asset_id, Asset.is_deleted.is_(False))
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_all(
        self, org_id: uuid.UUID, offset: int, limit: int,
        location_id: uuid.UUID | None = None, status: str | None = None,
    ) -> tuple[list[Asset], int]:
        stmt = select(Asset).where(Asset.org_id == org_id, Asset.is_deleted.is_(False))
        if location_id:
            stmt = stmt.where(Asset.location_id == location_id)
        if status:
            stmt = stmt.where(Asset.status == status)
        total = len((await self.db.execute(stmt)).scalars().all())
        stmt = stmt.offset(offset).limit(limit)
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total

    def add(self, asset: Asset) -> None:
        self.db.add(asset)


class EquipmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_asset(self, asset_id: uuid.UUID) -> list[Equipment]:
        stmt = select(Equipment).where(Equipment.asset_id == asset_id, Equipment.is_deleted.is_(False))
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_by_id(self, equipment_id: uuid.UUID) -> Equipment | None:
        stmt = select(Equipment).where(Equipment.id == equipment_id, Equipment.is_deleted.is_(False))
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def add(self, equipment: Equipment) -> None:
        self.db.add(equipment)


class CriticalityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def add(self, criticality: Criticality) -> None:
        self.db.add(criticality)

    async def history_for_asset(self, asset_id: uuid.UUID) -> list[Criticality]:
        stmt = select(Criticality).where(Criticality.asset_id == asset_id).order_by(Criticality.assessed_date.desc())
        return list((await self.db.execute(stmt)).scalars().all())

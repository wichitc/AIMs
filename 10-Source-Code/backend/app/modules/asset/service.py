import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import write_audit_log
from app.core.exceptions import ConflictError, NotFoundError
from app.modules.asset.models import Asset, Criticality, Equipment, Location
from app.modules.asset.repository import (
    AssetClassRepository,
    AssetRepository,
    CriticalityRepository,
    EquipmentRepository,
    LocationRepository,
)
from app.modules.asset.schemas import AssetCreate, CriticalityCreate, EquipmentCreate, LocationCreate

# Weights follow API 580 qualitative criticality ranking (safety-weighted).
_CRITICALITY_WEIGHTS = {"safety": 0.5, "environmental": 0.3, "economic": 0.2}


def _rank_from_score(score: float) -> str:
    if score >= 80:
        return "VeryHigh"
    if score >= 60:
        return "High"
    if score >= 35:
        return "Medium"
    return "Low"


class LocationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = LocationRepository(db)

    async def list_locations(self, org_id: uuid.UUID) -> list[Location]:
        return await self.repo.list_all(org_id)

    async def create_location(self, payload: LocationCreate, org_id: str, actor_id: str | None) -> Location:
        location = Location(org_id=uuid.UUID(org_id), **payload.model_dump())
        self.repo.add(location)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=org_id, action="Create",
            entity_type="Location", entity_id=location.id, new_value={"code": location.code},
        )
        await self.db.commit()
        return location


class AssetClassService:
    def __init__(self, db: AsyncSession):
        self.repo = AssetClassRepository(db)

    async def list_asset_classes(self):
        return await self.repo.list_all()


class AssetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.assets = AssetRepository(db)
        self.equipment = EquipmentRepository(db)

    async def create_asset(self, payload: AssetCreate, org_id: str, actor_id: str | None) -> Asset:
        existing = await self.assets.get_by_tag_number(payload.tag_number)
        if existing:
            raise ConflictError(f"Asset tag_number '{payload.tag_number}' already exists")

        asset = Asset(org_id=uuid.UUID(org_id), status="Operating", **payload.model_dump())
        self.assets.add(asset)
        await self.db.flush()

        await write_audit_log(
            self.db, user_id=actor_id, org_id=org_id, action="Create", entity_type="Asset",
            entity_id=asset.id, new_value={"tag_number": asset.tag_number, "name": asset.name},
        )
        await self.db.commit()
        return asset

    async def get_asset(self, asset_id: uuid.UUID) -> Asset:
        asset = await self.assets.get_by_id(asset_id)
        if not asset:
            raise NotFoundError(f"Asset {asset_id} not found")
        return asset

    async def list_assets(self, org_id: uuid.UUID, page: int, page_size: int, **filters):
        offset = (page - 1) * page_size
        return await self.assets.list_all(org_id, offset, page_size, **filters)

    async def list_equipment(self, asset_id: uuid.UUID) -> list[Equipment]:
        await self.get_asset(asset_id)  # 404 if asset doesn't exist
        return await self.equipment.list_by_asset(asset_id)

    async def add_equipment(self, asset_id: uuid.UUID, payload: EquipmentCreate, actor_id: str | None) -> Equipment:
        await self.get_asset(asset_id)
        equipment = Equipment(asset_id=asset_id, **payload.model_dump())
        self.equipment.add(equipment)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=None, action="Create", entity_type="Equipment",
            entity_id=equipment.id, new_value={"tag_number": equipment.tag_number, "level": equipment.level},
        )
        await self.db.commit()
        return equipment


class CriticalityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CriticalityRepository(db)
        self.assets = AssetRepository(db)

    async def assess(self, asset_id: uuid.UUID, payload: CriticalityCreate, actor_id: str | None) -> Criticality:
        asset = await self.assets.get_by_id(asset_id)
        if not asset:
            raise NotFoundError(f"Asset {asset_id} not found")

        calculated_score = (
            payload.safety_score * _CRITICALITY_WEIGHTS["safety"]
            + payload.environmental_score * _CRITICALITY_WEIGHTS["environmental"]
            + payload.economic_score * _CRITICALITY_WEIGHTS["economic"]
        )

        criticality = Criticality(
            asset_id=asset_id,
            safety_score=payload.safety_score,
            environmental_score=payload.environmental_score,
            economic_score=payload.economic_score,
            calculated_score=calculated_score,
            criticality_level=_rank_from_score(calculated_score),
            methodology=payload.methodology,
            assessed_date=payload.assessed_date,
            assessed_by=uuid.UUID(actor_id) if actor_id else None,
        )
        self.repo.add(criticality)
        await self.db.flush()

        asset.current_criticality_id = criticality.id
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(asset.org_id), action="Create", entity_type="Criticality",
            entity_id=criticality.id, new_value={"criticality_level": criticality.criticality_level},
        )
        await self.db.commit()
        return criticality

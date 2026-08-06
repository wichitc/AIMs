import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import PaginationMeta, ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.modules.asset.schemas import (
    AssetClassRead,
    AssetCreate,
    AssetRead,
    CriticalityCreate,
    CriticalityRead,
    EquipmentCreate,
    EquipmentRead,
    LocationCreate,
    LocationRead,
)
from app.modules.asset.service import AssetClassService, AssetService, CriticalityService, LocationService

router = APIRouter(tags=["Asset Management"])


@router.get("/assets", response_model=ResponseEnvelope[list[AssetRead]])
async def list_assets(
    page: int = 1,
    page_size: int = 20,
    location_id: uuid.UUID | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("asset.read")),
):
    assets, total = await AssetService(db).list_assets(
        uuid.UUID(current_user.org_id), page, page_size, location_id=location_id, status=status
    )
    return ResponseEnvelope(
        data=[AssetRead.model_validate(a, from_attributes=True) for a in assets],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.post("/assets", response_model=ResponseEnvelope[AssetRead], status_code=201)
async def create_asset(
    payload: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("asset.create")),
):
    asset = await AssetService(db).create_asset(payload, current_user.org_id, current_user.id)
    return ResponseEnvelope(data=AssetRead.model_validate(asset, from_attributes=True))


@router.get("/assets/{asset_id}", response_model=ResponseEnvelope[AssetRead])
async def get_asset(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("asset.read")),
):
    asset = await AssetService(db).get_asset(asset_id)
    return ResponseEnvelope(data=AssetRead.model_validate(asset, from_attributes=True))


@router.get("/assets/{asset_id}/equipment", response_model=ResponseEnvelope[list[EquipmentRead]])
async def list_equipment(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("asset.read")),
):
    equipment = await AssetService(db).list_equipment(asset_id)
    return ResponseEnvelope(data=[EquipmentRead.model_validate(e, from_attributes=True) for e in equipment])


@router.post("/assets/{asset_id}/equipment", response_model=ResponseEnvelope[EquipmentRead], status_code=201)
async def add_equipment(
    asset_id: uuid.UUID,
    payload: EquipmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("asset.update")),
):
    equipment = await AssetService(db).add_equipment(asset_id, payload, current_user.id)
    return ResponseEnvelope(data=EquipmentRead.model_validate(equipment, from_attributes=True))


@router.post("/assets/{asset_id}/criticality", response_model=ResponseEnvelope[CriticalityRead], status_code=201)
async def assess_criticality(
    asset_id: uuid.UUID,
    payload: CriticalityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("asset.update")),
):
    criticality = await CriticalityService(db).assess(asset_id, payload, current_user.id)
    return ResponseEnvelope(data=CriticalityRead.model_validate(criticality, from_attributes=True))


@router.get("/locations", response_model=ResponseEnvelope[list[LocationRead]])
async def list_locations(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("location.read")),
):
    locations = await LocationService(db).list_locations(uuid.UUID(current_user.org_id))
    return ResponseEnvelope(data=[LocationRead.model_validate(l, from_attributes=True) for l in locations])


@router.post("/locations", response_model=ResponseEnvelope[LocationRead], status_code=201)
async def create_location(
    payload: LocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("location.create")),
):
    location = await LocationService(db).create_location(payload, current_user.org_id, current_user.id)
    return ResponseEnvelope(data=LocationRead.model_validate(location, from_attributes=True))


@router.get("/asset-classes", response_model=ResponseEnvelope[list[AssetClassRead]])
async def list_asset_classes(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("asset.read")),
):
    classes = await AssetClassService(db).list_asset_classes()
    return ResponseEnvelope(data=[AssetClassRead.model_validate(c, from_attributes=True) for c in classes])

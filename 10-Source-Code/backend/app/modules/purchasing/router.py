import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.modules.purchasing.schemas import (
    MaterialCreate,
    MaterialRead,
    SupplierBlockUpdate,
    SupplierCreate,
    SupplierRead,
)
from app.modules.purchasing.service import MaterialService, SupplierService

router = APIRouter(tags=["Purchasing"])


@router.get("/materials", response_model=ResponseEnvelope[list[MaterialRead]])
async def list_materials(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("material.read")),
):
    materials = await MaterialService(db).list_materials(uuid.UUID(current_user.org_id))
    return ResponseEnvelope(data=[MaterialRead.model_validate(m, from_attributes=True) for m in materials])


@router.post("/materials", response_model=ResponseEnvelope[MaterialRead], status_code=201)
async def create_material(
    payload: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("material.create")),
):
    material = await MaterialService(db).create_material(payload, uuid.UUID(current_user.org_id), current_user.id)
    return ResponseEnvelope(data=MaterialRead.model_validate(material, from_attributes=True))


@router.get("/materials/{material_id}", response_model=ResponseEnvelope[MaterialRead])
async def get_material(
    material_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("material.read")),
):
    material = await MaterialService(db).get_material(material_id)
    return ResponseEnvelope(data=MaterialRead.model_validate(material, from_attributes=True))


@router.get("/suppliers", response_model=ResponseEnvelope[list[SupplierRead]])
async def list_suppliers(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("supplier.read")),
):
    suppliers = await SupplierService(db).list_suppliers(uuid.UUID(current_user.org_id))
    return ResponseEnvelope(data=[SupplierRead.model_validate(s, from_attributes=True) for s in suppliers])


@router.post("/suppliers", response_model=ResponseEnvelope[SupplierRead], status_code=201)
async def create_supplier(
    payload: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("supplier.create")),
):
    supplier = await SupplierService(db).create_supplier(payload, uuid.UUID(current_user.org_id), current_user.id)
    return ResponseEnvelope(data=SupplierRead.model_validate(supplier, from_attributes=True))


@router.get("/suppliers/{supplier_id}", response_model=ResponseEnvelope[SupplierRead])
async def get_supplier(
    supplier_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("supplier.read")),
):
    supplier = await SupplierService(db).get_supplier(supplier_id)
    return ResponseEnvelope(data=SupplierRead.model_validate(supplier, from_attributes=True))


@router.put("/suppliers/{supplier_id}/block", response_model=ResponseEnvelope[SupplierRead])
async def update_supplier_block(
    supplier_id: uuid.UUID,
    payload: SupplierBlockUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("supplier.create")),
):
    supplier = await SupplierService(db).update_block(supplier_id, payload, current_user.id)
    return ResponseEnvelope(data=SupplierRead.model_validate(supplier, from_attributes=True))

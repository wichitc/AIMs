import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.modules.purchasing.schemas import (
    MaterialCreate,
    MaterialRead,
    PurchasingInfoRecordCreate,
    PurchasingInfoRecordRead,
    QuotaArrangementCreate,
    QuotaArrangementRead,
    SourceCandidateRead,
    SourceListEntryCreate,
    SourceListEntryRead,
    SupplierBlockUpdate,
    SupplierCreate,
    SupplierRead,
)
from app.modules.purchasing.service import (
    MaterialService,
    PurchasingInfoRecordService,
    QuotaArrangementService,
    SourceDeterminationService,
    SourceListEntryService,
    SupplierService,
)

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


@router.get("/purchasing-info-records", response_model=ResponseEnvelope[list[PurchasingInfoRecordRead]])
async def list_purchasing_info_records(
    material_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("sourcing.read")),
):
    records = await PurchasingInfoRecordService(db).list_for_material(uuid.UUID(current_user.org_id), material_id)
    return ResponseEnvelope(data=[PurchasingInfoRecordRead.model_validate(r, from_attributes=True) for r in records])


@router.post(
    "/purchasing-info-records", response_model=ResponseEnvelope[PurchasingInfoRecordRead], status_code=201
)
async def create_purchasing_info_record(
    payload: PurchasingInfoRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("sourcing.create")),
):
    record = await PurchasingInfoRecordService(db).create(payload, uuid.UUID(current_user.org_id), current_user.id)
    return ResponseEnvelope(data=PurchasingInfoRecordRead.model_validate(record, from_attributes=True))


@router.get("/source-list-entries", response_model=ResponseEnvelope[list[SourceListEntryRead]])
async def list_source_list_entries(
    material_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("sourcing.read")),
):
    entries = await SourceListEntryService(db).list_for_material(uuid.UUID(current_user.org_id), material_id)
    return ResponseEnvelope(data=[SourceListEntryRead.model_validate(e, from_attributes=True) for e in entries])


@router.post("/source-list-entries", response_model=ResponseEnvelope[SourceListEntryRead], status_code=201)
async def create_source_list_entry(
    payload: SourceListEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("sourcing.create")),
):
    entry = await SourceListEntryService(db).create(payload, uuid.UUID(current_user.org_id), current_user.id)
    return ResponseEnvelope(data=SourceListEntryRead.model_validate(entry, from_attributes=True))


@router.get("/quota-arrangements", response_model=ResponseEnvelope[list[QuotaArrangementRead]])
async def list_quota_arrangements(
    material_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("sourcing.read")),
):
    arrangements = await QuotaArrangementService(db).list_for_material(uuid.UUID(current_user.org_id), material_id)
    return ResponseEnvelope(data=[QuotaArrangementRead.model_validate(a, from_attributes=True) for a in arrangements])


@router.post("/quota-arrangements", response_model=ResponseEnvelope[QuotaArrangementRead], status_code=201)
async def create_quota_arrangement(
    payload: QuotaArrangementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("sourcing.create")),
):
    arrangement = await QuotaArrangementService(db).create(payload, uuid.UUID(current_user.org_id), current_user.id)
    return ResponseEnvelope(data=QuotaArrangementRead.model_validate(arrangement, from_attributes=True))


@router.get("/source-determination", response_model=ResponseEnvelope[list[SourceCandidateRead]])
async def run_source_determination(
    material_id: uuid.UUID,
    as_of: date | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("sourcing.read")),
):
    candidates = await SourceDeterminationService(db).determine(
        uuid.UUID(current_user.org_id), material_id, as_of or date.today()
    )
    return ResponseEnvelope(data=[SourceCandidateRead.model_validate(c, from_attributes=True) for c in candidates])

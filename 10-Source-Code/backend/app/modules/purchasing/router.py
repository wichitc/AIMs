import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import PaginationMeta, ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.modules.purchasing.schemas import (
    MaterialCreate,
    MaterialRead,
    PurchaseOrderConfirm,
    PurchaseOrderRead,
    PurchaseRequisitionCreate,
    PurchaseRequisitionDecision,
    PurchaseRequisitionRead,
    PurchasingInfoRecordCreate,
    PurchasingInfoRecordRead,
    QuotaArrangementCreate,
    QuotaArrangementRead,
    QuotationCreate,
    QuotationRead,
    RFQCreate,
    RFQInviteCreate,
    RFQInviteRead,
    RFQRead,
    SourceCandidateRead,
    SourceListEntryCreate,
    SourceListEntryRead,
    SupplierBlockUpdate,
    SupplierCreate,
    SupplierRead,
)
from app.modules.purchasing.service import (
    MaterialService,
    PurchaseOrderService,
    PurchaseRequisitionService,
    PurchasingInfoRecordService,
    QuotaArrangementService,
    QuotationService,
    RFQService,
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


@router.get("/purchase-requisitions", response_model=ResponseEnvelope[list[PurchaseRequisitionRead]])
async def list_purchase_requisitions(
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("purchase_requisition.read")),
):
    requisitions, total = await PurchaseRequisitionService(db).list_requisitions(
        uuid.UUID(current_user.org_id), status, page, page_size
    )
    return ResponseEnvelope(
        data=[PurchaseRequisitionRead.model_validate(r, from_attributes=True) for r in requisitions],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.post("/purchase-requisitions", response_model=ResponseEnvelope[PurchaseRequisitionRead], status_code=201)
async def create_purchase_requisition(
    payload: PurchaseRequisitionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("purchase_requisition.create")),
):
    requisition = await PurchaseRequisitionService(db).create_requisition(
        payload, uuid.UUID(current_user.org_id), current_user.id
    )
    return ResponseEnvelope(data=PurchaseRequisitionRead.model_validate(requisition, from_attributes=True))


@router.get("/purchase-requisitions/{requisition_id}", response_model=ResponseEnvelope[PurchaseRequisitionRead])
async def get_purchase_requisition(
    requisition_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("purchase_requisition.read")),
):
    requisition = await PurchaseRequisitionService(db).get_requisition(requisition_id)
    return ResponseEnvelope(data=PurchaseRequisitionRead.model_validate(requisition, from_attributes=True))


@router.post(
    "/purchase-requisitions/{requisition_id}/submit", response_model=ResponseEnvelope[PurchaseRequisitionRead]
)
async def submit_purchase_requisition(
    requisition_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("purchase_requisition.create")),
):
    requisition = await PurchaseRequisitionService(db).submit(requisition_id, current_user.id)
    return ResponseEnvelope(data=PurchaseRequisitionRead.model_validate(requisition, from_attributes=True))


@router.post(
    "/purchase-requisitions/{requisition_id}/approve", response_model=ResponseEnvelope[PurchaseRequisitionRead]
)
async def approve_purchase_requisition(
    requisition_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("purchase_requisition.approve")),
):
    requisition = await PurchaseRequisitionService(db).approve(requisition_id, current_user.id)
    return ResponseEnvelope(data=PurchaseRequisitionRead.model_validate(requisition, from_attributes=True))


@router.post(
    "/purchase-requisitions/{requisition_id}/reject", response_model=ResponseEnvelope[PurchaseRequisitionRead]
)
async def reject_purchase_requisition(
    requisition_id: uuid.UUID,
    payload: PurchaseRequisitionDecision,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("purchase_requisition.approve")),
):
    requisition = await PurchaseRequisitionService(db).reject(requisition_id, current_user.id, payload.reason)
    return ResponseEnvelope(data=PurchaseRequisitionRead.model_validate(requisition, from_attributes=True))


@router.post(
    "/purchase-requisitions/{requisition_id}/withdraw", response_model=ResponseEnvelope[PurchaseRequisitionRead]
)
async def withdraw_purchase_requisition(
    requisition_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("purchase_requisition.create")),
):
    requisition = await PurchaseRequisitionService(db).withdraw(requisition_id, current_user.id)
    return ResponseEnvelope(data=PurchaseRequisitionRead.model_validate(requisition, from_attributes=True))


@router.get("/rfqs", response_model=ResponseEnvelope[list[RFQRead]])
async def list_rfqs(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("rfq.read")),
):
    rfqs = await RFQService(db).list_rfqs(uuid.UUID(current_user.org_id))
    return ResponseEnvelope(data=[RFQRead.model_validate(r, from_attributes=True) for r in rfqs])


@router.post("/rfqs", response_model=ResponseEnvelope[RFQRead], status_code=201)
async def create_rfq(
    payload: RFQCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("rfq.create")),
):
    rfq = await RFQService(db).create_rfq(payload, uuid.UUID(current_user.org_id), current_user.id)
    return ResponseEnvelope(data=RFQRead.model_validate(rfq, from_attributes=True))


@router.get("/rfqs/{rfq_id}", response_model=ResponseEnvelope[RFQRead])
async def get_rfq(
    rfq_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("rfq.read")),
):
    rfq = await RFQService(db).get_rfq(rfq_id)
    return ResponseEnvelope(data=RFQRead.model_validate(rfq, from_attributes=True))


@router.post("/rfqs/{rfq_id}/invite", response_model=ResponseEnvelope[RFQInviteRead], status_code=201)
async def invite_supplier(
    rfq_id: uuid.UUID,
    payload: RFQInviteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("rfq.create")),
):
    invite = await RFQService(db).invite_supplier(rfq_id, payload.supplier_id, current_user.id)
    return ResponseEnvelope(data=RFQInviteRead.model_validate(invite, from_attributes=True))


@router.get("/rfqs/{rfq_id}/invites", response_model=ResponseEnvelope[list[RFQInviteRead]])
async def list_invites(
    rfq_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("rfq.read")),
):
    invites = await RFQService(db).list_invites(rfq_id)
    return ResponseEnvelope(data=[RFQInviteRead.model_validate(i, from_attributes=True) for i in invites])


@router.post("/rfqs/{rfq_id}/dispatch", response_model=ResponseEnvelope[RFQRead])
async def dispatch_rfq(
    rfq_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("rfq.create")),
):
    rfq = await RFQService(db).dispatch(rfq_id, current_user.id)
    return ResponseEnvelope(data=RFQRead.model_validate(rfq, from_attributes=True))


@router.get("/quotations", response_model=ResponseEnvelope[list[QuotationRead]])
async def list_quotations(
    rfq_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("quotation.read")),
):
    quotations = await QuotationService(db).list_for_rfq(rfq_id)
    return ResponseEnvelope(data=[QuotationRead.model_validate(q, from_attributes=True) for q in quotations])


@router.post("/quotations", response_model=ResponseEnvelope[QuotationRead], status_code=201)
async def create_quotation(
    payload: QuotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("quotation.create")),
):
    quotation = await QuotationService(db).create_quotation(payload, uuid.UUID(current_user.org_id), current_user.id)
    return ResponseEnvelope(data=QuotationRead.model_validate(quotation, from_attributes=True))


@router.post("/quotation-items/{item_id}/award", response_model=ResponseEnvelope[None])
async def award_quotation_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("quotation.create")),
):
    await QuotationService(db).award_item(item_id, current_user.id)
    return ResponseEnvelope(data=None)


@router.post("/rfqs/{rfq_id}/convert-to-purchase-orders", response_model=ResponseEnvelope[list[PurchaseOrderRead]])
async def convert_rfq_to_purchase_orders(
    rfq_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("purchase_order.create")),
):
    orders = await PurchaseOrderService(db).convert_from_rfq(rfq_id, uuid.UUID(current_user.org_id), current_user.id)
    return ResponseEnvelope(data=[PurchaseOrderRead.model_validate(o, from_attributes=True) for o in orders])


@router.get("/purchase-orders", response_model=ResponseEnvelope[list[PurchaseOrderRead]])
async def list_purchase_orders(
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("purchase_order.read")),
):
    orders, total = await PurchaseOrderService(db).list_orders(uuid.UUID(current_user.org_id), status, page, page_size)
    return ResponseEnvelope(
        data=[PurchaseOrderRead.model_validate(o, from_attributes=True) for o in orders],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.get("/purchase-orders/{order_id}", response_model=ResponseEnvelope[PurchaseOrderRead])
async def get_purchase_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("purchase_order.read")),
):
    order = await PurchaseOrderService(db).get_order(order_id)
    return ResponseEnvelope(data=PurchaseOrderRead.model_validate(order, from_attributes=True))


@router.post("/purchase-orders/{order_id}/approve", response_model=ResponseEnvelope[PurchaseOrderRead])
async def approve_purchase_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("purchase_order.approve")),
):
    order = await PurchaseOrderService(db).approve(order_id, current_user.id)
    return ResponseEnvelope(data=PurchaseOrderRead.model_validate(order, from_attributes=True))


@router.post("/purchase-orders/{order_id}/send", response_model=ResponseEnvelope[PurchaseOrderRead])
async def send_purchase_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("purchase_order.create")),
):
    order = await PurchaseOrderService(db).send(order_id, current_user.id)
    return ResponseEnvelope(data=PurchaseOrderRead.model_validate(order, from_attributes=True))


@router.post("/purchase-orders/{order_id}/confirm", response_model=ResponseEnvelope[PurchaseOrderRead])
async def confirm_purchase_order(
    order_id: uuid.UUID,
    payload: PurchaseOrderConfirm,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("purchase_order.create")),
):
    order = await PurchaseOrderService(db).confirm(order_id, payload.confirmed_date, current_user.id)
    return ResponseEnvelope(data=PurchaseOrderRead.model_validate(order, from_attributes=True))

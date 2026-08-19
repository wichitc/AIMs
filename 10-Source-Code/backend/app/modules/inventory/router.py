import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.modules.inventory.schemas import (
    GoodsIssueCreate,
    GoodsReceiptCreate,
    MaterialDocumentRead,
    ReservationCreate,
    ReservationRead,
    StockBalanceRead,
    StockTransferIssueCreate,
    StockTransferOneStepCreate,
    StockTransferRead,
)
from app.modules.inventory.service import (
    MovementPostingService,
    ReservationService,
    StockOverviewService,
    StockTransferService,
)

router = APIRouter(tags=["Inventory"])


@router.post("/goods-receipts", response_model=ResponseEnvelope[MaterialDocumentRead], status_code=201)
async def post_goods_receipt(
    payload: GoodsReceiptCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("goods_receipt.create")),
):
    document = await MovementPostingService(db).post_goods_receipt(
        payload, uuid.UUID(current_user.org_id), current_user.id
    )
    return ResponseEnvelope(data=MaterialDocumentRead.model_validate(document, from_attributes=True))


@router.get("/material-documents/{document_id}", response_model=ResponseEnvelope[MaterialDocumentRead])
async def get_material_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inventory.read")),
):
    document = await MovementPostingService(db).get_document(document_id)
    return ResponseEnvelope(data=MaterialDocumentRead.model_validate(document, from_attributes=True))


@router.post("/material-documents/{document_id}/reverse", response_model=ResponseEnvelope[MaterialDocumentRead])
async def reverse_material_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("goods_receipt.create")),
):
    reversal = await MovementPostingService(db).reverse_document(document_id, current_user.id)
    return ResponseEnvelope(data=MaterialDocumentRead.model_validate(reversal, from_attributes=True))


@router.get("/purchase-orders/{order_id}/material-documents", response_model=ResponseEnvelope[list[MaterialDocumentRead]])
async def list_material_documents_for_po(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inventory.read")),
):
    documents = await MovementPostingService(db).list_documents_for_po(order_id)
    return ResponseEnvelope(data=[MaterialDocumentRead.model_validate(d, from_attributes=True) for d in documents])


@router.get("/stock-balances", response_model=ResponseEnvelope[list[StockBalanceRead]])
async def list_stock_balances(
    material_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inventory.read")),
):
    balances = await StockOverviewService(db).list_balances(material_id)
    return ResponseEnvelope(data=[StockBalanceRead.model_validate(b, from_attributes=True) for b in balances])


@router.get("/reservations", response_model=ResponseEnvelope[list[ReservationRead]])
async def list_reservations(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inventory.read")),
):
    reservations = await ReservationService(db).list_reservations(uuid.UUID(current_user.org_id), status)
    return ResponseEnvelope(data=[ReservationRead.model_validate(r, from_attributes=True) for r in reservations])


@router.post("/reservations", response_model=ResponseEnvelope[ReservationRead], status_code=201)
async def create_reservation(
    payload: ReservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inventory.create")),
):
    reservation = await ReservationService(db).create_reservation(
        payload, uuid.UUID(current_user.org_id), current_user.id
    )
    return ResponseEnvelope(data=ReservationRead.model_validate(reservation, from_attributes=True))


@router.post("/reservations/{reservation_id}/cancel", response_model=ResponseEnvelope[ReservationRead])
async def cancel_reservation(
    reservation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inventory.create")),
):
    reservation = await ReservationService(db).cancel_reservation(reservation_id, current_user.id)
    return ResponseEnvelope(data=ReservationRead.model_validate(reservation, from_attributes=True))


@router.post("/goods-issues", response_model=ResponseEnvelope[MaterialDocumentRead], status_code=201)
async def post_goods_issue(
    payload: GoodsIssueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inventory.create")),
):
    document = await MovementPostingService(db).post_goods_issue(
        payload, uuid.UUID(current_user.org_id), current_user.id
    )
    return ResponseEnvelope(data=MaterialDocumentRead.model_validate(document, from_attributes=True))


@router.get("/stock-transfers", response_model=ResponseEnvelope[list[StockTransferRead]])
async def list_stock_transfers(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inventory.read")),
):
    transfers = await StockTransferService(db).list_transfers(uuid.UUID(current_user.org_id), status)
    return ResponseEnvelope(data=[StockTransferRead.model_validate(t, from_attributes=True) for t in transfers])


@router.post("/stock-transfers/one-step", response_model=ResponseEnvelope[StockTransferRead], status_code=201)
async def post_one_step_transfer(
    payload: StockTransferOneStepCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inventory.create")),
):
    transfer = await MovementPostingService(db).post_one_step_transfer(
        payload, uuid.UUID(current_user.org_id), current_user.id
    )
    return ResponseEnvelope(data=StockTransferRead.model_validate(transfer, from_attributes=True))


@router.post("/stock-transfers/issue", response_model=ResponseEnvelope[StockTransferRead], status_code=201)
async def post_transfer_issue(
    payload: StockTransferIssueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inventory.create")),
):
    transfer = await MovementPostingService(db).post_transfer_issue(
        payload, uuid.UUID(current_user.org_id), current_user.id
    )
    return ResponseEnvelope(data=StockTransferRead.model_validate(transfer, from_attributes=True))


@router.post("/stock-transfers/{transfer_id}/receive", response_model=ResponseEnvelope[StockTransferRead])
async def post_transfer_receipt(
    transfer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("inventory.create")),
):
    transfer = await MovementPostingService(db).post_transfer_receipt(transfer_id, current_user.id)
    return ResponseEnvelope(data=StockTransferRead.model_validate(transfer, from_attributes=True))

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.modules.inventory.schemas import GoodsReceiptCreate, MaterialDocumentRead, StockBalanceRead
from app.modules.inventory.service import MovementPostingService, StockOverviewService

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
    reversal = await MovementPostingService(db).reverse_goods_receipt(document_id, current_user.id)
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

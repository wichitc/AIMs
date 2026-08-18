import uuid
from datetime import date

from pydantic import BaseModel, Field


class GoodsReceiptCreate(BaseModel):
    po_item_id: uuid.UUID
    storage_location_id: uuid.UUID
    # unit_price is deliberately absent — a GR posts at the PO item's locked-in price, never
    # a freely-entered value (SAP MM FR-015 valuation integrity; letting the receiver name
    # their own price would be a valuation-manipulation vector).
    quantity: float = Field(gt=0)


class MaterialDocumentItemRead(BaseModel):
    id: uuid.UUID
    line_no: int
    material_id: uuid.UUID
    storage_location_id: uuid.UUID
    quantity: float
    unit_price: float
    po_item_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class MaterialDocumentRead(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    movement_type: str
    posted_date: date
    reference_type: str | None
    reference_id: uuid.UUID | None
    reversal_of_id: uuid.UUID | None
    items: list[MaterialDocumentItemRead]

    model_config = {"from_attributes": True}


class StockBalanceRead(BaseModel):
    id: uuid.UUID
    material_id: uuid.UUID
    storage_location_id: uuid.UUID
    quantity: float
    value: float

    model_config = {"from_attributes": True}

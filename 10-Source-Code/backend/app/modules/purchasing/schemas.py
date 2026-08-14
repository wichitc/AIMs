import uuid
from datetime import date

from pydantic import BaseModel, Field


class MaterialCreate(BaseModel):
    # org_id is deliberately absent — derived server-side from the caller's JWT (SEC-007
    # pattern, see LocationCreate/UserCreate).
    material_number: str = Field(max_length=50)
    name: str = Field(max_length=200)
    description: str | None = None
    material_type: str = Field(pattern="^(SparePart|Consumable|RawMaterial|Service)$")
    material_group: str | None = None
    base_uom: str = Field(max_length=10)
    min_stock_level: float | None = Field(default=None, ge=0)


class MaterialRead(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    material_number: str
    name: str
    description: str | None
    material_type: str
    material_group: str | None
    base_uom: str
    moving_average_price: float | None
    min_stock_level: float | None
    is_active: bool

    model_config = {"from_attributes": True}


class SupplierCreate(BaseModel):
    supplier_number: str = Field(max_length=50)
    name: str = Field(max_length=200)
    tax_id: str | None = None
    country: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    payment_terms: str | None = None
    currency: str = Field(default="USD", max_length=3)


class SupplierRead(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    supplier_number: str
    name: str
    tax_id: str | None
    country: str | None
    email: str | None
    phone: str | None
    address: str | None
    payment_terms: str | None
    currency: str
    is_active: bool
    is_blocked: bool
    block_reason: str | None

    model_config = {"from_attributes": True}


class SupplierBlockUpdate(BaseModel):
    is_blocked: bool
    block_reason: str | None = None


class PurchasingInfoRecordCreate(BaseModel):
    material_id: uuid.UUID
    supplier_id: uuid.UUID
    price: float = Field(gt=0)
    lead_time_days: int | None = Field(default=None, ge=0)
    valid_from: date | None = None
    valid_to: date | None = None


class PurchasingInfoRecordRead(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    material_id: uuid.UUID
    supplier_id: uuid.UUID
    price: float
    lead_time_days: int | None
    valid_from: date | None
    valid_to: date | None
    is_active: bool

    model_config = {"from_attributes": True}


class SourceListEntryCreate(BaseModel):
    material_id: uuid.UUID
    supplier_id: uuid.UUID
    is_fixed: bool = False
    is_blocked: bool = False
    valid_from: date | None = None
    valid_to: date | None = None


class SourceListEntryRead(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    material_id: uuid.UUID
    supplier_id: uuid.UUID
    is_fixed: bool
    is_blocked: bool
    valid_from: date | None
    valid_to: date | None

    model_config = {"from_attributes": True}


class QuotaArrangementCreate(BaseModel):
    material_id: uuid.UUID
    supplier_id: uuid.UUID
    quota_percentage: float = Field(gt=0, le=100)
    valid_from: date | None = None
    valid_to: date | None = None


class QuotaArrangementRead(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    material_id: uuid.UUID
    supplier_id: uuid.UUID
    quota_percentage: float
    valid_from: date | None
    valid_to: date | None

    model_config = {"from_attributes": True}


class SourceCandidateRead(BaseModel):
    supplier_id: uuid.UUID
    rank: int
    reason: str
    price: float | None

import uuid

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

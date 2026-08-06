import uuid
from datetime import date

from pydantic import BaseModel, Field


class LocationCreate(BaseModel):
    org_id: uuid.UUID
    parent_location_id: uuid.UUID | None = None
    level: str = Field(pattern="^(Plant|Area|Unit)$")
    name: str = Field(max_length=200)
    code: str = Field(max_length=50)
    latitude: float | None = None
    longitude: float | None = None


class LocationRead(BaseModel):
    id: uuid.UUID
    parent_location_id: uuid.UUID | None
    level: str
    name: str
    code: str

    model_config = {"from_attributes": True}


class AssetClassRead(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    category: str

    model_config = {"from_attributes": True}


class AssetCreate(BaseModel):
    location_id: uuid.UUID
    asset_class_id: uuid.UUID
    tag_number: str = Field(max_length=50)
    name: str = Field(max_length=200)
    design_code: str | None = None
    design_pressure_bar: float | None = None
    design_temperature_c: float | None = None
    material: str | None = None
    install_date: date | None = None


class AssetUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    design_pressure_bar: float | None = None
    design_temperature_c: float | None = None


class AssetRead(BaseModel):
    id: uuid.UUID
    location_id: uuid.UUID
    asset_class_id: uuid.UUID
    tag_number: str
    name: str
    status: str
    design_code: str | None
    install_date: date | None

    model_config = {"from_attributes": True}


class EquipmentCreate(BaseModel):
    parent_equipment_id: uuid.UUID | None = None
    level: str = Field(pattern="^(Component|InspectionPoint)$")
    tag_number: str = Field(max_length=50)
    name: str = Field(max_length=200)
    cml_number: str | None = None
    nominal_thickness_mm: float | None = None
    minimum_required_thickness_mm: float | None = None


class EquipmentRead(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    parent_equipment_id: uuid.UUID | None
    level: str
    tag_number: str
    name: str
    cml_number: str | None

    model_config = {"from_attributes": True}


class CriticalityCreate(BaseModel):
    safety_score: float
    environmental_score: float
    economic_score: float
    assessed_date: date
    methodology: str | None = None


class CriticalityRead(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    calculated_score: float
    criticality_level: str
    assessed_date: date

    model_config = {"from_attributes": True}

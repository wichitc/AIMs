import uuid
from datetime import date

from pydantic import BaseModel, Field


class LocationCreate(BaseModel):
    # org_id is deliberately absent — it's derived server-side from the caller's JWT
    # (see LocationService.create_location), never accepted from the client. It was
    # missing this guard until now; matches the pattern every other *Create schema uses
    # (see AssetCreate) and SecurityTest.md SEC-007.
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
    latitude: float | None
    longitude: float | None

    model_config = {"from_attributes": True}


class AssetClassCreate(BaseModel):
    name: str = Field(max_length=100)
    code: str = Field(max_length=30)
    category: str = Field(
        pattern="^(PressureVessel|Piping|Tank|Rotating|Static|Instrument|Electrical)$"
    )
    description: str | None = None


class AssetClassRead(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    category: str
    description: str | None

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
    design_pressure_bar: float | None
    design_temperature_c: float | None
    material: str | None
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
    nominal_thickness_mm: float | None
    minimum_required_thickness_mm: float | None

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

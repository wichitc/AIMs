import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.modules.condition_monitoring.models import SensorData

router = APIRouter(tags=["Condition Monitoring"])


class SensorDataCreate(BaseModel):
    equipment_id: uuid.UUID
    sensor_type: str = Field(pattern="^(Temperature|Pressure|Vibration|Flow)$")
    value: float
    unit: str
    reading_timestamp: datetime
    source: str = Field(pattern="^(MQTT|OPC-UA|Modbus)$")


class SensorDataRead(BaseModel):
    equipment_id: uuid.UUID
    sensor_type: str
    value: float
    unit: str
    reading_timestamp: datetime
    source: str

    model_config = {"from_attributes": True}


@router.post("/sensor-data", response_model=ResponseEnvelope[SensorDataRead], status_code=201)
async def ingest_sensor_data(
    payload: SensorDataCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("sensor.write")),
):
    """Ingested directly by MQTT/OPC-UA/Modbus bridge service accounts, or via this endpoint for testing."""
    record = SensorData(**payload.model_dump())
    db.add(record)
    await db.commit()
    return ResponseEnvelope(data=SensorDataRead.model_validate(record, from_attributes=True))


@router.get("/equipment/{equipment_id}/sensor-data", response_model=ResponseEnvelope[list[SensorDataRead]])
async def query_sensor_data(
    equipment_id: uuid.UUID,
    sensor_type: str | None = None,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("sensor.read")),
):
    stmt = select(SensorData).where(SensorData.equipment_id == equipment_id)
    if sensor_type:
        stmt = stmt.where(SensorData.sensor_type == sensor_type)
    if from_ts:
        stmt = stmt.where(SensorData.reading_timestamp >= from_ts)
    if to_ts:
        stmt = stmt.where(SensorData.reading_timestamp <= to_ts)
    stmt = stmt.order_by(SensorData.reading_timestamp.desc()).limit(1000)

    rows = (await db.execute(stmt)).scalars().all()
    return ResponseEnvelope(data=[SensorDataRead.model_validate(r, from_attributes=True) for r in rows])


@router.get("/equipment/{equipment_id}/sensor-data/latest", response_model=ResponseEnvelope[list[SensorDataRead]])
async def latest_sensor_readings(
    equipment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("sensor.read")),
):
    latest_readings: dict[str, SensorData] = {}
    stmt = (
        select(SensorData)
        .where(SensorData.equipment_id == equipment_id)
        .order_by(SensorData.reading_timestamp.desc())
        .limit(500)
    )
    for row in (await db.execute(stmt)).scalars().all():
        latest_readings.setdefault(row.sensor_type, row)

    return ResponseEnvelope(data=[SensorDataRead.model_validate(r, from_attributes=True) for r in latest_readings.values()])

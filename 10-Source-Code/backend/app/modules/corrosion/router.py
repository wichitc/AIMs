import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.modules.corrosion.schemas import CorrosionRecordRead, ThicknessRecordCreate, ThicknessRecordRead
from app.modules.corrosion.service import CorrosionCalculationService, ThicknessRecordService

router = APIRouter(tags=["Corrosion Management"])


@router.get("/equipment/{equipment_id}/thickness-records", response_model=ResponseEnvelope[list[ThicknessRecordRead]])
async def list_thickness_records(
    equipment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("corrosion.read")),
):
    readings = await ThicknessRecordService(db).list_readings(equipment_id)
    return ResponseEnvelope(data=[ThicknessRecordRead.model_validate(r, from_attributes=True) for r in readings])


@router.post(
    "/equipment/{equipment_id}/thickness-records",
    response_model=ResponseEnvelope[ThicknessRecordRead],
    status_code=201,
)
async def add_thickness_record(
    equipment_id: uuid.UUID,
    payload: ThicknessRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("corrosion.create")),
):
    record = await ThicknessRecordService(db).add_reading(equipment_id, payload, current_user.id)
    return ResponseEnvelope(data=ThicknessRecordRead.model_validate(record, from_attributes=True))


@router.get("/equipment/{equipment_id}/corrosion-records", response_model=ResponseEnvelope[list[CorrosionRecordRead]])
async def list_corrosion_records(
    equipment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("corrosion.read")),
):
    records = await CorrosionCalculationService(db).list_records(equipment_id)
    return ResponseEnvelope(data=[CorrosionRecordRead.model_validate(r, from_attributes=True) for r in records])


@router.post(
    "/equipment/{equipment_id}/corrosion-records/calculate",
    response_model=ResponseEnvelope[CorrosionRecordRead],
)
async def calculate_corrosion_record(
    equipment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("corrosion.create")),
):
    record = await CorrosionCalculationService(db).calculate(equipment_id, current_user.id)
    return ResponseEnvelope(data=CorrosionRecordRead.model_validate(record, from_attributes=True))

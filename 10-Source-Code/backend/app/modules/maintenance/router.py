import uuid
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import write_audit_log
from app.common.response import PaginationMeta, ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.core.exceptions import NotFoundError
from app.modules.maintenance.models import MaintenanceOrder

router = APIRouter(tags=["Maintenance"])


class MaintenanceOrderCreate(BaseModel):
    equipment_id: uuid.UUID
    defect_id: uuid.UUID | None = None
    order_type: str = Field(pattern="^(Corrective|Preventive|Predictive)$")
    description: str
    priority: str = Field(default="Medium", pattern="^(Low|Medium|High|Urgent)$")
    scheduled_date: date | None = None
    assigned_to: uuid.UUID | None = None
    cost_estimate: float | None = None


class MaintenanceOrderUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(Open|InProgress|Completed|Cancelled)$")
    completed_date: date | None = None


class MaintenanceOrderRead(BaseModel):
    id: uuid.UUID
    equipment_id: uuid.UUID
    defect_id: uuid.UUID | None
    order_type: str
    status: str
    priority: str
    scheduled_date: date | None
    completed_date: date | None

    model_config = {"from_attributes": True}


@router.get("/maintenance-orders", response_model=ResponseEnvelope[list[MaintenanceOrderRead]])
async def list_maintenance_orders(
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("maintenance.read")),
):
    stmt = select(MaintenanceOrder)
    if status:
        stmt = stmt.where(MaintenanceOrder.status == status)
    total = len((await db.execute(stmt)).scalars().all())
    rows = (await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return ResponseEnvelope(
        data=[MaintenanceOrderRead.model_validate(r, from_attributes=True) for r in rows],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.post("/maintenance-orders", response_model=ResponseEnvelope[MaintenanceOrderRead], status_code=201)
async def create_maintenance_order(
    payload: MaintenanceOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("maintenance.create")),
):
    order = MaintenanceOrder(status="Open", **payload.model_dump())
    db.add(order)
    await db.flush()
    await write_audit_log(
        db, user_id=current_user.id, org_id=None, action="Create", entity_type="MaintenanceOrder",
        entity_id=order.id, new_value={"order_type": order.order_type},
    )
    await db.commit()
    return ResponseEnvelope(data=MaintenanceOrderRead.model_validate(order, from_attributes=True))


@router.put("/maintenance-orders/{order_id}", response_model=ResponseEnvelope[MaintenanceOrderRead])
async def update_maintenance_order(
    order_id: uuid.UUID,
    payload: MaintenanceOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("maintenance.update")),
):
    order = (await db.execute(select(MaintenanceOrder).where(MaintenanceOrder.id == order_id))).scalar_one_or_none()
    if not order:
        raise NotFoundError(f"Maintenance order {order_id} not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(order, field, value)

    await write_audit_log(
        db, user_id=current_user.id, org_id=None, action="Update", entity_type="MaintenanceOrder",
        entity_id=order.id, new_value=payload.model_dump(exclude_unset=True, mode="json"),
    )
    await db.commit()
    return ResponseEnvelope(data=MaintenanceOrderRead.model_validate(order, from_attributes=True))

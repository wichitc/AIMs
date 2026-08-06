import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import PaginationMeta, ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.modules.audit_log.models import AuditLog

router = APIRouter(tags=["Audit Log"])


class AuditLogRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID
    old_value: dict | None
    new_value: dict | None
    timestamp: datetime

    model_config = {"from_attributes": True}


@router.get("/audit-logs", response_model=ResponseEnvelope[list[AuditLogRead]])
async def query_audit_logs(
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("audit.read")),
):
    stmt = select(AuditLog)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    stmt = stmt.order_by(AuditLog.timestamp.desc())

    total = len((await db.execute(stmt)).scalars().all())
    rows = (await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return ResponseEnvelope(
        data=[AuditLogRead.model_validate(r, from_attributes=True) for r in rows],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )

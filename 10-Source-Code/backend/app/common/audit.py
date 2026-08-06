import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit_log.models import AuditLog


async def write_audit_log(
    db: AsyncSession,
    *,
    user_id: str | None,
    org_id: str | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    old_value: dict | None = None,
    new_value: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """Append-only audit trail write. Called from the service layer on every mutation."""
    log = AuditLog(
        user_id=uuid.UUID(user_id) if user_id else None,
        org_id=uuid.UUID(org_id) if org_id else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
    )
    db.add(log)
    # Deliberately not committed here — caller's transaction controls the commit boundary
    # so the audit row and the business change succeed or fail atomically together.

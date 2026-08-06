import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class AuditMixin:
    """created_by/updated_by point at user.id on every table, including `organization` and
    `user` themselves — that closes a circular FK dependency (organization.created_by -> user.id,
    user.org_id -> organization.id) that breaks CREATE TABLE ordering. `use_alter=True` defers
    these two FKs to a post-creation ALTER TABLE so Alembic/SQLAlchemy can resolve table order
    for everything else normally. Surfaced by `alembic revision --autogenerate` against a real
    database — see Deployment.md §3."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", use_alter=True, name="fk_created_by_user")
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", use_alter=True, name="fk_updated_by_user")
    )


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

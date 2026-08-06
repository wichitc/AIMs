import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, Text, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.core.database import Base


class DocumentEmbedding(Base):
    """RAG knowledge base. See AI-Copilot-Design.md §7 — new table added to support the AI Copilot,
    not part of the original Phase 2 schema."""

    __tablename__ = "document_embedding"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dimensions), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


async def upsert_embedding(
    db: AsyncSession, *, org_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID, content: str, embedding: list[float]
) -> DocumentEmbedding:
    existing = (
        await db.execute(
            select(DocumentEmbedding).where(
                DocumentEmbedding.entity_type == entity_type, DocumentEmbedding.entity_id == entity_id
            )
        )
    ).scalar_one_or_none()

    if existing:
        existing.content = content
        existing.embedding = embedding
        return existing

    record = DocumentEmbedding(
        org_id=org_id, entity_type=entity_type, entity_id=entity_id, content=content, embedding=embedding
    )
    db.add(record)
    return record


async def similarity_search(
    db: AsyncSession, *, org_id: uuid.UUID, query_embedding: list[float], top_k: int = 8
) -> list[DocumentEmbedding]:
    """Cosine-distance nearest-neighbor search, hard-scoped to org_id — the RBAC boundary
    for RAG retrieval (AI-Copilot-Design.md §6). Never accepts org_id from client input."""
    stmt = (
        select(DocumentEmbedding)
        .where(DocumentEmbedding.org_id == org_id)
        .order_by(DocumentEmbedding.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    return list((await db.execute(stmt)).scalars().all())

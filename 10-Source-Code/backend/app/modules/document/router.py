import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.core.exceptions import NotFoundError
from app.modules.document.models import Document

router = APIRouter(tags=["Document Management"])


class DocumentMetadataCreate(BaseModel):
    """Metadata registered after the binary is uploaded to object storage by the client
    via a pre-signed URL — the API never proxies file bytes directly."""

    asset_id: uuid.UUID | None = None
    equipment_id: uuid.UUID | None = None
    inspection_id: uuid.UUID | None = None
    document_type: str
    file_name: str
    storage_key: str
    mime_type: str | None = None
    file_size_bytes: int | None = None


class DocumentRead(BaseModel):
    id: uuid.UUID
    document_type: str
    file_name: str
    version: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}


@router.get("/documents", response_model=ResponseEnvelope[list[DocumentRead]])
async def list_documents(
    asset_id: uuid.UUID | None = None,
    document_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("document.read")),
):
    stmt = select(Document).where(Document.is_deleted.is_(False))
    if asset_id:
        stmt = stmt.where(Document.asset_id == asset_id)
    if document_type:
        stmt = stmt.where(Document.document_type == document_type)
    rows = (await db.execute(stmt)).scalars().all()
    return ResponseEnvelope(data=[DocumentRead.model_validate(r, from_attributes=True) for r in rows])


@router.post("/documents", response_model=ResponseEnvelope[DocumentRead], status_code=201)
async def register_document(
    payload: DocumentMetadataCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("document.create")),
):
    doc = Document(
        org_id=uuid.UUID(current_user.org_id),
        uploaded_by=uuid.UUID(current_user.id),
        uploaded_at=datetime.now(timezone.utc),
        **payload.model_dump(),
    )
    db.add(doc)
    await db.commit()
    return ResponseEnvelope(data=DocumentRead.model_validate(doc, from_attributes=True))


@router.get("/documents/{document_id}", response_model=ResponseEnvelope[DocumentRead])
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("document.read")),
):
    doc = (
        await db.execute(select(Document).where(Document.id == document_id, Document.is_deleted.is_(False)))
    ).scalar_one_or_none()
    if not doc:
        raise NotFoundError(f"Document {document_id} not found")
    return ResponseEnvelope(data=DocumentRead.model_validate(doc, from_attributes=True))

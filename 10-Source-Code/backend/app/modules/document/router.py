import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import write_audit_log
from app.common.response import ResponseEnvelope
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_permission
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.modules.document.models import Document

router = APIRouter(tags=["Document Management"])

# Files this small demo/reference deployment accepts — matches BRD §8 document types
# (P&ID, drawings, certificates, inspection reports) plus common office/image formats.
_ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx", ".dwg"}
_MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB


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
    asset_id: uuid.UUID | None
    document_type: str
    file_name: str
    version: int
    file_size_bytes: int | None
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
    await db.flush()
    await write_audit_log(
        db, user_id=current_user.id, org_id=current_user.org_id, action="Create", entity_type="Document",
        entity_id=doc.id, new_value={"file_name": doc.file_name, "document_type": doc.document_type},
    )
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


@router.post("/documents/upload", response_model=ResponseEnvelope[DocumentRead], status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    asset_id: uuid.UUID | None = Form(None),
    equipment_id: uuid.UUID | None = Form(None),
    inspection_id: uuid.UUID | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("document.create")),
):
    """Accepts the file directly (see the storage-location note on
    settings.document_storage_path for why this differs from the metadata-only
    /documents endpoint above). Validates extension and size before touching disk."""
    original_name = file.filename or "upload"
    extension = Path(original_name).suffix.lower()
    if extension not in _ALLOWED_EXTENSIONS:
        raise BusinessRuleError(
            f"File type '{extension or '(none)'}' is not allowed",
            details=[{"field": "file", "issue": "unsupported_extension", "allowed": sorted(_ALLOWED_EXTENSIONS)}],
        )

    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise BusinessRuleError(
            f"File exceeds the {_MAX_UPLOAD_BYTES // (1024 * 1024)} MB upload limit",
            details=[{"field": "file", "issue": "too_large"}],
        )

    storage_dir = Path(settings.document_storage_path)
    storage_dir.mkdir(parents=True, exist_ok=True)
    # The stored filename is always a fresh UUID, never the client-supplied name — avoids
    # path traversal / collision entirely; the original name is kept only as display metadata.
    storage_key = f"{uuid.uuid4()}{extension}"
    (storage_dir / storage_key).write_bytes(content)

    doc = Document(
        org_id=uuid.UUID(current_user.org_id),
        asset_id=asset_id,
        equipment_id=equipment_id,
        inspection_id=inspection_id,
        document_type=document_type,
        file_name=original_name,
        storage_key=storage_key,
        mime_type=file.content_type,
        file_size_bytes=len(content),
        uploaded_by=uuid.UUID(current_user.id),
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(doc)
    await db.flush()
    await write_audit_log(
        db, user_id=current_user.id, org_id=current_user.org_id, action="Create", entity_type="Document",
        entity_id=doc.id, new_value={"file_name": doc.file_name, "document_type": doc.document_type, "file_size_bytes": doc.file_size_bytes},
    )
    await db.commit()
    return ResponseEnvelope(data=DocumentRead.model_validate(doc, from_attributes=True))


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("document.read")),
):
    doc = (
        await db.execute(select(Document).where(Document.id == document_id, Document.is_deleted.is_(False)))
    ).scalar_one_or_none()
    if not doc:
        raise NotFoundError(f"Document {document_id} not found")

    file_path = Path(settings.document_storage_path) / doc.storage_key
    if not file_path.is_file():
        raise NotFoundError(f"Stored file for document {document_id} is missing on disk")

    return FileResponse(path=file_path, filename=doc.file_name, media_type=doc.mime_type or "application/octet-stream")

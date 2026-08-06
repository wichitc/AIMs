import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AIPrediction(Base):
    """Owned and written by the AI service (see Database.md — AI service has write access here,
    Core API has read access for display)."""

    __tablename__ = "ai_prediction"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    equipment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    prediction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    predicted_value: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    input_features: Mapped[dict | None] = mapped_column(JSON)
    predicted_for_date: Mapped[date | None] = mapped_column(Date)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

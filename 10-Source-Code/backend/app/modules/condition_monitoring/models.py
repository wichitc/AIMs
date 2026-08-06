import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SensorData(Base):
    """TimescaleDB hypertable — partitioned on reading_timestamp.

    Migration must run: SELECT create_hypertable('sensor_data', 'reading_timestamp');
    Immutable/append-only: no updated_at, no soft delete.
    """

    __tablename__ = "sensor_data"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    equipment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False)
    sensor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(10), nullable=False)
    reading_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    quality_flag: Mapped[str] = mapped_column(String(10), default="Good")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

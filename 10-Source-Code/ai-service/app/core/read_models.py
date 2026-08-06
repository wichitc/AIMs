"""Read-only mirrors of Core API tables that the AI service queries directly for RAG
context and predictions. These tables are owned and migrated by the Core API
(see 10-Source-Code/backend/app/modules/*/models.py) — this service never writes to them.
Only the columns the AI service actually needs are declared.
"""

import uuid
from datetime import date

from sqlalchemy import Date, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Asset(Base):
    __tablename__ = "asset"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    tag_number: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20))


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    tag_number: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))


class RiskAssessment(Base):
    __tablename__ = "risk_assessment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    assessment_date: Mapped[date] = mapped_column(Date)
    pof_score: Mapped[float] = mapped_column(Numeric(6, 3))
    risk_score: Mapped[float] = mapped_column(Numeric(8, 3))
    risk_rank: Mapped[str] = mapped_column(String(20))
    next_inspection_date: Mapped[date | None] = mapped_column(Date)


class Finding(Base):
    __tablename__ = "finding"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    equipment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    finding_type: Mapped[str] = mapped_column(String(30))
    severity: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
    raised_date: Mapped[date] = mapped_column(Date)


class CorrosionRecord(Base):
    __tablename__ = "corrosion_record"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    equipment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    assessment_date: Mapped[date] = mapped_column(Date)
    governing_rate_mm_yr: Mapped[float] = mapped_column(Numeric(8, 4))
    remaining_life_years: Mapped[float] = mapped_column(Numeric(6, 2))
    next_inspection_date: Mapped[date] = mapped_column(Date)

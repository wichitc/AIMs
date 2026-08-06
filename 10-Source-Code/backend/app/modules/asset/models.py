import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.base_model import AuditMixin, SoftDeleteMixin, UUIDMixin
from app.core.database import Base


class Location(Base, UUIDMixin, AuditMixin):
    __tablename__ = "location"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=False)
    parent_location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("location.id"))
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # Plant | Area | Unit
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6))


class AssetClass(Base, UUIDMixin, AuditMixin):
    __tablename__ = "asset_class"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(String)


class Criticality(Base, UUIDMixin, AuditMixin):
    __tablename__ = "criticality"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("asset.id"), nullable=False)
    safety_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    environmental_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    economic_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    calculated_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    criticality_level: Mapped[str] = mapped_column(String(20), nullable=False)
    methodology: Mapped[str | None] = mapped_column(String(50))
    assessed_date: Mapped[date] = mapped_column(Date, nullable=False)
    assessed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"))


class Asset(Base, UUIDMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "asset"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=False)
    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("location.id"), nullable=False)
    asset_class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset_class.id"), nullable=False
    )
    # asset <-> criticality is a deliberate circular "current pointer" (asset points at its
    # latest criticality row; criticality points back at its asset) — use_alter=True defers
    # this FK past CREATE TABLE so it doesn't block table-creation ordering. Same fix as the
    # organization/user cycle in common/base_model.py.
    current_criticality_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("criticality.id", use_alter=True, name="fk_asset_current_criticality")
    )
    tag_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    design_code: Mapped[str | None] = mapped_column(String(50))
    design_pressure_bar: Mapped[float | None] = mapped_column(Numeric(10, 2))
    design_temperature_c: Mapped[float | None] = mapped_column(Numeric(10, 2))
    material: Mapped[str | None] = mapped_column(String(100))
    install_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Operating")

    equipment: Mapped[list["Equipment"]] = relationship(back_populates="asset")


class Equipment(Base, UUIDMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "equipment"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("asset.id"), nullable=False)
    parent_equipment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("equipment.id"))
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # Component | InspectionPoint
    tag_number: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    cml_number: Mapped[str | None] = mapped_column(String(30))
    nominal_thickness_mm: Mapped[float | None] = mapped_column(Numeric(8, 3))
    minimum_required_thickness_mm: Mapped[float | None] = mapped_column(Numeric(8, 3))

    asset: Mapped["Asset"] = relationship(back_populates="equipment")

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import write_audit_log
from app.core.exceptions import ConflictError, NotFoundError
from app.modules.purchasing.models import Material, Supplier
from app.modules.purchasing.repository import MaterialRepository, SupplierRepository
from app.modules.purchasing.schemas import MaterialCreate, SupplierBlockUpdate, SupplierCreate


class MaterialService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MaterialRepository(db)

    async def list_materials(self, org_id: uuid.UUID) -> list[Material]:
        return await self.repo.list_all(org_id)

    async def get_material(self, material_id: uuid.UUID) -> Material:
        material = await self.repo.get_by_id(material_id)
        if not material:
            raise NotFoundError(f"Material {material_id} not found")
        return material

    async def create_material(self, payload: MaterialCreate, org_id: uuid.UUID, actor_id: str | None) -> Material:
        existing = await self.repo.get_by_number(org_id, payload.material_number)
        if existing:
            raise ConflictError(f"Material number '{payload.material_number}' already exists")

        material = Material(org_id=org_id, **payload.model_dump())
        self.repo.add(material)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="Material",
            entity_id=material.id, new_value={"material_number": material.material_number, "name": material.name},
        )
        await self.db.commit()
        return material


class SupplierService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SupplierRepository(db)

    async def list_suppliers(self, org_id: uuid.UUID) -> list[Supplier]:
        return await self.repo.list_all(org_id)

    async def get_supplier(self, supplier_id: uuid.UUID) -> Supplier:
        supplier = await self.repo.get_by_id(supplier_id)
        if not supplier:
            raise NotFoundError(f"Supplier {supplier_id} not found")
        return supplier

    async def create_supplier(self, payload: SupplierCreate, org_id: uuid.UUID, actor_id: str | None) -> Supplier:
        existing = await self.repo.get_by_number(org_id, payload.supplier_number)
        if existing:
            raise ConflictError(f"Supplier number '{payload.supplier_number}' already exists")

        supplier = Supplier(org_id=org_id, **payload.model_dump())
        self.repo.add(supplier)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org_id), action="Create", entity_type="Supplier",
            entity_id=supplier.id, new_value={"supplier_number": supplier.supplier_number, "name": supplier.name},
        )
        await self.db.commit()
        return supplier

    async def update_block(
        self, supplier_id: uuid.UUID, payload: SupplierBlockUpdate, actor_id: str | None
    ) -> Supplier:
        supplier = await self.get_supplier(supplier_id)
        supplier.is_blocked = payload.is_blocked
        supplier.block_reason = payload.block_reason if payload.is_blocked else None
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(supplier.org_id), action="Update", entity_type="Supplier",
            entity_id=supplier.id, new_value={"is_blocked": supplier.is_blocked, "block_reason": supplier.block_reason},
        )
        await self.db.commit()
        return supplier

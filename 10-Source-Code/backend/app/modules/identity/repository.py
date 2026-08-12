import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.identity.models import Organization, Permission, Role, RolePermission, User, UserRole


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = (
            select(User)
            .where(User.id == user_id, User.is_deleted.is_(False))
            .options(selectinload(User.roles).selectinload(UserRole.role))
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        stmt = (
            select(User)
            .where(User.username == username, User.is_deleted.is_(False))
            .options(selectinload(User.roles).selectinload(UserRole.role))
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_all(self, org_id: uuid.UUID | None, offset: int, limit: int) -> tuple[list[User], int]:
        stmt = select(User).where(User.is_deleted.is_(False))
        if org_id:
            stmt = stmt.where(User.org_id == org_id)
        total = len((await self.db.execute(stmt)).scalars().all())
        stmt = stmt.offset(offset).limit(limit).options(selectinload(User.roles).selectinload(UserRole.role))
        rows = (await self.db.execute(stmt)).scalars().all()
        return list(rows), total

    def add(self, user: User) -> None:
        self.db.add(user)

    async def get_permission_codes(self, user_id: uuid.UUID) -> list[str]:
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id)
        )
        return list((await self.db.execute(stmt)).scalars().all())


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[Role]:
        stmt = select(Role).options(selectinload(Role.permissions).selectinload(RolePermission.permission))
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_by_id(self, role_id: uuid.UUID) -> Role | None:
        stmt = (
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions).selectinload(RolePermission.permission))
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def add(self, role: Role) -> None:
        self.db.add(role)


class PermissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[Permission]:
        stmt = select(Permission).order_by(Permission.module, Permission.action)
        return list((await self.db.execute(stmt)).scalars().all())


class RolePermissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def replace_for_role(self, role_id: uuid.UUID, permission_ids: list[uuid.UUID]) -> None:
        await self.db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
        for permission_id in permission_ids:
            self.db.add(RolePermission(role_id=role_id, permission_id=permission_id))


class OrganizationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[Organization]:
        return list((await self.db.execute(select(Organization))).scalars().all())

    async def get_by_code(self, code: str) -> Organization | None:
        return (
            await self.db.execute(select(Organization).where(Organization.code == code))
        ).scalar_one_or_none()

    def add(self, org: Organization) -> None:
        self.db.add(org)

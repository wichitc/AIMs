import uuid

from sqlalchemy import select
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

    async def list(self, org_id: uuid.UUID | None, offset: int, limit: int) -> tuple[list[User], int]:
        stmt = select(User).where(User.is_deleted.is_(False))
        if org_id:
            stmt = stmt.where(User.org_id == org_id)
        total = len((await self.db.execute(stmt)).scalars().all())
        stmt = stmt.offset(offset).limit(limit)
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

    async def list(self) -> list[Role]:
        return list((await self.db.execute(select(Role))).scalars().all())

    async def get_by_id(self, role_id: uuid.UUID) -> Role | None:
        return (await self.db.execute(select(Role).where(Role.id == role_id))).scalar_one_or_none()

    def add(self, role: Role) -> None:
        self.db.add(role)


class OrganizationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self) -> list[Organization]:
        return list((await self.db.execute(select(Organization))).scalars().all())

    async def get_by_code(self, code: str) -> Organization | None:
        return (
            await self.db.execute(select(Organization).where(Organization.code == code))
        ).scalar_one_or_none()

    def add(self, org: Organization) -> None:
        self.db.add(org)

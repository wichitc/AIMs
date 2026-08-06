import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.audit import write_audit_log
from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.modules.identity.models import Organization, Role, User
from app.modules.identity.repository import OrganizationRepository, RoleRepository, UserRepository
from app.modules.identity.schemas import OrganizationCreate, RoleCreate, TokenResponse, UserCreate, UserRead


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)

    async def login(self, username: str, password: str) -> TokenResponse:
        user = await self.users.get_by_username(username)
        if not user or not user.password_hash or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid username or password")
        if not user.is_active:
            raise UnauthorizedError("Account is disabled")

        role_names = [ur.role.name for ur in user.roles]
        permission_codes = await self.users.get_permission_codes(user.id)

        access_token = create_access_token(
            user_id=str(user.id), org_id=str(user.org_id), roles=role_names, permissions=permission_codes
        )
        refresh_token = create_refresh_token(user_id=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,
            user=UserRead(
                id=user.id,
                org_id=user.org_id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                roles=role_names,
            ),
        )


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)

    async def create_user(self, payload: UserCreate, actor_id: str | None) -> User:
        existing = await self.users.get_by_username(payload.username)
        if existing:
            raise ConflictError(f"Username '{payload.username}' is already taken")

        user = User(
            org_id=payload.org_id,
            username=payload.username,
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            phone=payload.phone,
        )
        self.users.add(user)
        await self.db.flush()

        await write_audit_log(
            self.db,
            user_id=actor_id,
            org_id=str(payload.org_id),
            action="Create",
            entity_type="User",
            entity_id=user.id,
            new_value={"username": user.username, "email": user.email},
        )
        await self.db.commit()
        return user

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self.users.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    async def list_users(self, org_id: uuid.UUID | None, page: int, page_size: int):
        offset = (page - 1) * page_size
        return await self.users.list_all(org_id, offset, page_size)


class RoleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.roles = RoleRepository(db)

    async def list_roles(self) -> list[Role]:
        return await self.roles.list_all()

    async def create_role(self, payload: RoleCreate, actor_id: str | None) -> Role:
        role = Role(name=payload.name, description=payload.description)
        self.roles.add(role)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=None, action="Create", entity_type="Role", entity_id=role.id,
            new_value={"name": role.name},
        )
        await self.db.commit()
        return role


class OrganizationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.orgs = OrganizationRepository(db)

    async def list_organizations(self) -> list[Organization]:
        return await self.orgs.list_all()

    async def create_organization(self, payload: OrganizationCreate, actor_id: str | None) -> Organization:
        existing = await self.orgs.get_by_code(payload.code)
        if existing:
            raise ConflictError(f"Organization code '{payload.code}' already exists")

        org = Organization(
            parent_org_id=payload.parent_org_id,
            name=payload.name,
            code=payload.code,
            org_type=payload.org_type,
            address=payload.address,
        )
        self.orgs.add(org)
        await self.db.flush()
        await write_audit_log(
            self.db, user_id=actor_id, org_id=str(org.id), action="Create", entity_type="Organization",
            entity_id=org.id, new_value={"code": org.code, "name": org.name},
        )
        await self.db.commit()
        return org

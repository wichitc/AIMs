import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import PaginationMeta, ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.identity.models import Role, User
from app.modules.identity.schemas import (
    LoginRequest,
    OrganizationCreate,
    OrganizationRead,
    PermissionRead,
    RoleCreate,
    RolePermissionsUpdate,
    RoleRead,
    TokenResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.modules.identity.service import AuthService, OrganizationService, RoleService, UserService


def _role_read(role: Role) -> RoleRead:
    return RoleRead(
        id=role.id, name=role.name, description=role.description, is_system_role=role.is_system_role,
        permission_codes=[rp.permission.code for rp in role.permissions],
    )


def _user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id, org_id=user.org_id, username=user.username, email=user.email,
        full_name=user.full_name, is_active=user.is_active,
        roles=[ur.role.name for ur in user.roles],
    )

router = APIRouter(tags=["Identity & Access Management"])


@router.post("/auth/login", response_model=ResponseEnvelope[TokenResponse])
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await AuthService(db).login(payload.username, payload.password)
    return ResponseEnvelope(data=result)


@router.get("/users", response_model=ResponseEnvelope[list[UserRead]])
async def list_users(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("user.read")),
):
    users, total = await UserService(db).list_users(uuid.UUID(current_user.org_id), page, page_size)
    return ResponseEnvelope(
        # UserRead.roles is list[str] (role names), but User.roles is the list[UserRole]
        # join relationship — model_validate can't bridge that automatically (it tried to
        # coerce UserRole objects into strings and crashed on the unloaded relationship
        # before that). Build the role-name list explicitly instead.
        data=[
            UserRead(
                id=u.id, org_id=u.org_id, username=u.username, email=u.email,
                full_name=u.full_name, is_active=u.is_active,
                roles=[ur.role.name for ur in u.roles],
            )
            for u in users
        ],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.post("/users", response_model=ResponseEnvelope[UserRead], status_code=201)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("user.create")),
):
    user = await UserService(db).create_user(payload, uuid.UUID(current_user.org_id), actor_id=current_user.id)
    return ResponseEnvelope(data=UserRead.model_validate(user, from_attributes=True))


@router.put("/users/{user_id}", response_model=ResponseEnvelope[UserRead])
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("user.create")),
):
    user = await UserService(db).update_user(user_id, payload, actor_id=current_user.id)
    return ResponseEnvelope(data=_user_read(user))


@router.get("/users/me", response_model=ResponseEnvelope[UserRead])
async def get_me(db: AsyncSession = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    user = await UserService(db).get_user(uuid.UUID(current_user.id))
    return ResponseEnvelope(
        data=UserRead(
            id=user.id, org_id=user.org_id, username=user.username, email=user.email,
            full_name=user.full_name, is_active=user.is_active, roles=current_user.roles,
        )
    )


@router.get("/roles", response_model=ResponseEnvelope[list[RoleRead]])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("role.read")),
):
    roles = await RoleService(db).list_roles()
    return ResponseEnvelope(data=[_role_read(r) for r in roles])


@router.post("/roles", response_model=ResponseEnvelope[RoleRead], status_code=201)
async def create_role(
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("role.create")),
):
    role = await RoleService(db).create_role(payload, actor_id=current_user.id)
    return ResponseEnvelope(data=_role_read(role))


@router.get("/permissions", response_model=ResponseEnvelope[list[PermissionRead]])
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("role.read")),
):
    permissions = await RoleService(db).list_permissions()
    return ResponseEnvelope(data=[PermissionRead.model_validate(p, from_attributes=True) for p in permissions])


@router.put("/roles/{role_id}/permissions", response_model=ResponseEnvelope[RoleRead])
async def update_role_permissions(
    role_id: uuid.UUID,
    payload: RolePermissionsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("role.create")),
):
    role = await RoleService(db).update_role_permissions(role_id, payload.permission_ids, actor_id=current_user.id)
    return ResponseEnvelope(data=_role_read(role))


@router.get("/organizations", response_model=ResponseEnvelope[list[OrganizationRead]])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("organization.read")),
):
    orgs = await OrganizationService(db).list_organizations()
    return ResponseEnvelope(data=[OrganizationRead.model_validate(o, from_attributes=True) for o in orgs])


@router.post("/organizations", response_model=ResponseEnvelope[OrganizationRead], status_code=201)
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("organization.create")),
):
    org = await OrganizationService(db).create_organization(payload, actor_id=current_user.id)
    return ResponseEnvelope(data=OrganizationRead.model_validate(org, from_attributes=True))

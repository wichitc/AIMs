import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import PaginationMeta, ResponseEnvelope
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.identity.schemas import (
    LoginRequest,
    OrganizationCreate,
    OrganizationRead,
    RoleCreate,
    RoleRead,
    TokenResponse,
    UserCreate,
    UserRead,
)
from app.modules.identity.service import AuthService, OrganizationService, RoleService, UserService

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
        data=[UserRead.model_validate(u, from_attributes=True) for u in users],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


@router.post("/users", response_model=ResponseEnvelope[UserRead], status_code=201)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("user.create")),
):
    user = await UserService(db).create_user(payload, actor_id=current_user.id)
    return ResponseEnvelope(data=UserRead.model_validate(user, from_attributes=True))


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
    return ResponseEnvelope(data=[RoleRead.model_validate(r, from_attributes=True) for r in roles])


@router.post("/roles", response_model=ResponseEnvelope[RoleRead], status_code=201)
async def create_role(
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("role.create")),
):
    role = await RoleService(db).create_role(payload, actor_id=current_user.id)
    return ResponseEnvelope(data=RoleRead.model_validate(role, from_attributes=True))


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

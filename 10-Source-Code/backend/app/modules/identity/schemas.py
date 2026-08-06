import uuid

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    username: str
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: "UserRead"


class UserCreate(BaseModel):
    org_id: uuid.UUID
    username: str = Field(max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(max_length=200)
    phone: str | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class UserRead(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    username: str
    email: str
    full_name: str
    is_active: bool
    roles: list[str] = []

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = None


class RoleRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_system_role: bool

    model_config = {"from_attributes": True}


class RolePermissionsUpdate(BaseModel):
    permission_ids: list[uuid.UUID]


class OrganizationCreate(BaseModel):
    parent_org_id: uuid.UUID | None = None
    name: str = Field(max_length=200)
    code: str = Field(max_length=50)
    org_type: str = Field(pattern="^(Corporate|BusinessUnit|Plant)$")
    address: str | None = None


class OrganizationRead(BaseModel):
    id: uuid.UUID
    parent_org_id: uuid.UUID | None
    name: str
    code: str
    org_type: str

    model_config = {"from_attributes": True}

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


class CurrentUser(BaseModel):
    id: str
    org_id: str
    roles: list[str]
    permissions: list[str]


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise UnauthorizedError("Invalid or expired access token") from exc

    if payload.get("type") != "access":
        raise UnauthorizedError("Token is not an access token")

    return CurrentUser(
        id=payload["sub"],
        org_id=payload.get("org_id", ""),
        roles=payload.get("roles", []),
        permissions=payload.get("permissions", []),
    )


def require_permission(permission_code: str):
    """FastAPI dependency factory enforcing RBAC at the route level.

    Usage: `Depends(require_permission("asset.create"))`
    """

    def _check(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if permission_code not in current_user.permissions:
            raise ForbiddenError(f"Missing required permission: {permission_code}")
        return current_user

    return _check

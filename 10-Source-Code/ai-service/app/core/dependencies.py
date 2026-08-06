from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings

# tokenUrl points at the Core API — this service only verifies tokens issued there.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://core-api/v1/auth/login")


class CurrentUser(BaseModel):
    id: str
    org_id: str
    roles: list[str]
    permissions: list[str]


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired access token") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Token is not an access token")

    return CurrentUser(
        id=payload["sub"],
        org_id=payload.get("org_id", ""),
        roles=payload.get("roles", []),
        permissions=payload.get("permissions", []),
    )


def require_permission(permission_code: str):
    def _check(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if permission_code not in current_user.permissions:
            raise HTTPException(status_code=403, detail=f"Missing required permission: {permission_code}")
        return current_user

    return _check

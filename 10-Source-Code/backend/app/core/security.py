from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# Calls bcrypt directly rather than through passlib.CryptContext — passlib 1.7.4 is
# unmaintained and its bcrypt backend-detection code is broken against modern bcrypt
# releases (AttributeError: module 'bcrypt' has no attribute '__about__'). Verified by
# actually running the seed script end-to-end; direct bcrypt has no such issue.
_BCRYPT_MAX_BYTES = 72  # bcrypt silently ignores/errors past this — truncate deliberately


def hash_password(password: str) -> str:
    truncated = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(truncated, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    truncated = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(truncated, password_hash.encode("utf-8"))


def _create_token(subject: str, claims: dict[str, Any], expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {**claims, "sub": subject, "iat": now, "exp": now + expires_delta}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str, org_id: str, roles: list[str], permissions: list[str]) -> str:
    return _create_token(
        subject=user_id,
        claims={"org_id": org_id, "roles": roles, "permissions": permissions, "type": "access"},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(
        subject=user_id,
        claims={"type": "refresh"},
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

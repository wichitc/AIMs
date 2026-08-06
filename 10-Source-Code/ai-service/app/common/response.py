from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    """Matches the Core API's envelope (see backend/app/common/response.py and API-Spec.md
    §1.2) so frontend clients handle both services identically."""

    success: bool = True
    data: T | None = None
    error: dict | None = None

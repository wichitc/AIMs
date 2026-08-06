from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int = 0


class ResponseEnvelope(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    meta: PaginationMeta | None = None
    error: dict | None = None


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

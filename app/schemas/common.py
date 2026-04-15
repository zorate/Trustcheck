from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorInfo(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorInfo] = None
    meta: Optional[dict[str, Any]] = None

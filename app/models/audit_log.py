from datetime import datetime, timezone
from typing import Any, Optional
import uuid

from beanie import Document, Indexed
from pydantic import Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def new_uuid() -> str:
    return str(uuid.uuid4())


class AuditLog(Document):
    id: str = Field(default_factory=new_uuid)
    business_id: Optional[Indexed(str)] = None  # type: ignore[valid-type]
    actor_id: Optional[str] = None
    action: Indexed(str)                         # type: ignore[valid-type]
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    detail: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "audit_logs"
        indexes = [
            "business_id",
            "actor_id",
            "action",
            "resource_type",
            "created_at",
            [("business_id", 1), ("created_at", -1)],
        ]
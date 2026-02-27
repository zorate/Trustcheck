from datetime import datetime, timezone
from typing import Optional
import uuid

from beanie import Document, Indexed
from pydantic import Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def new_uuid() -> str:
    return str(uuid.uuid4())


class Person(Document):
    id: str = Field(default_factory=new_uuid)
    business_id: Indexed(str)  # type: ignore[valid-type]
    phone_hash: str
    phone_display: str
    full_name: str
    capacity_level: str = "none"
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    deleted_at: Optional[datetime] = None

    class Settings:
        name = "persons"
        indexes = [
            "business_id",
            "phone_hash",
            "is_active",
            [("business_id", 1), ("phone_hash", 1)],
        ]
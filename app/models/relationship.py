from datetime import datetime, timezone
from typing import Optional
import uuid

from beanie import Document, Indexed
from pydantic import Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def new_uuid() -> str:
    return str(uuid.uuid4())


class Relationship(Document):
    id: str = Field(default_factory=new_uuid)
    business_id: Indexed(str)  # type: ignore[valid-type]
    person_id: Indexed(str)    # type: ignore[valid-type]
    relationship_type: str
    relationship_start: datetime
    relationship_end: Optional[datetime] = None
    status: str = "active"
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    deleted_at: Optional[datetime] = None

    class Settings:
        name = "relationships"
        indexes = [
            "business_id",
            "person_id",
            [("business_id", 1), ("person_id", 1)],
            "status",
        ]
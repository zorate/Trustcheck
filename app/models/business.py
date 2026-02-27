from datetime import datetime, timezone
from typing import Optional
import uuid

from beanie import Document, Indexed
from pydantic import Field, EmailStr


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def new_uuid() -> str:
    return str(uuid.uuid4())


class Business(Document):
    id: str = Field(default_factory=new_uuid)
    name: str
    email: Indexed(EmailStr, unique=True)  # type: ignore[valid-type]
    phone: Optional[str] = None
    address: Optional[str] = None
    business_type: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    deleted_at: Optional[datetime] = None

    class Settings:
        name = "businesses"
        indexes = ["email", "is_active", "created_at"]
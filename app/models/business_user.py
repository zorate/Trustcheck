from datetime import datetime, timezone
from typing import Optional
import uuid

from beanie import Document, Indexed
from pydantic import Field, EmailStr


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def new_uuid() -> str:
    return str(uuid.uuid4())


class BusinessUser(Document):
    id: str = Field(default_factory=new_uuid)
    business_id: Indexed(str)  # type: ignore[valid-type]
    email: Indexed(EmailStr, unique=True)  # type: ignore[valid-type]
    full_name: str
    hashed_password: str
    role: str = "staff"
    is_active: bool = True
    last_login_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    deleted_at: Optional[datetime] = None

    class Settings:
        name = "business_users"
        indexes = [
            "business_id",
            "email",
            "is_active",
            [("business_id", 1), ("email", 1)],
        ]
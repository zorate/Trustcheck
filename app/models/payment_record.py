from datetime import datetime, timezone
from typing import Optional
import uuid

from beanie import Document, Indexed
from pydantic import Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def new_uuid() -> str:
    return str(uuid.uuid4())


class PaymentRecord(Document):
    id: str = Field(default_factory=new_uuid)
    business_id: Indexed(str)  # type: ignore[valid-type]
    person_id: Indexed(str)    # type: ignore[valid-type]
    relationship_id: str
    amount: int
    currency: str = "NGN"
    description: str
    due_date: datetime
    paid_date: Optional[datetime] = None
    status: str = "pending"
    created_by: str
    updated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    deleted_at: Optional[datetime] = None

    class Settings:
        name = "payment_records"
        indexes = [
            "business_id",
            "person_id",
            "relationship_id",
            "status",
            "due_date",
            [("business_id", 1), ("person_id", 1)],
            [("business_id", 1), ("person_id", 1), ("status", 1)],
        ]
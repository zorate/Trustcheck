from datetime import datetime, timezone
from typing import Optional
import uuid

from beanie import Document, Indexed
from pydantic import Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def new_uuid() -> str:
    return str(uuid.uuid4())


class TrustScore(Document):
    id: str = Field(default_factory=new_uuid)
    business_id: Indexed(str)  # type: ignore[valid-type]
    person_id: Indexed(str)    # type: ignore[valid-type]
    payment_history_score: int = 0
    consistency_score: int = 0
    duration_score: int = 0
    capacity_score: int = 0
    reference_score: int = 0
    total_score: int = 0
    risk_band: str = "high_risk"
    recommendation: str = "Do not extend credit"
    cold_start: bool = True
    payment_count: int = 0
    computed_at: datetime = Field(default_factory=utcnow)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "trust_scores"
        indexes = [
            "business_id",
            "person_id",
            [("business_id", 1), ("person_id", 1)],
            "computed_at",
        ]
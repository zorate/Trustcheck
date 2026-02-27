from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class RecordPaymentRequest(BaseModel):
    person_id: str
    relationship_id: str
    amount: int = Field(..., gt=0, description="Amount in smallest currency unit (e.g., kobo)")
    currency: str = Field("NGN", max_length=3)
    description: str = Field(..., min_length=1, max_length=500)
    due_date: datetime
    paid_date: Optional[datetime] = None
    status: str = Field("pending", description="pending | paid | late | missed")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"pending", "paid", "late", "missed"}
        if v not in allowed:
            raise ValueError(f"status must be one of: {', '.join(allowed)}")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper()


class UpdatePaymentStatusRequest(BaseModel):
    status: str
    paid_date: Optional[datetime] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"pending", "paid", "late", "missed"}
        if v not in allowed:
            raise ValueError(f"status must be one of: {', '.join(allowed)}")
        return v


class PaymentOut(BaseModel):
    id: str
    business_id: str
    person_id: str
    relationship_id: str
    amount: int
    currency: str
    description: str
    due_date: datetime
    paid_date: Optional[datetime] = None
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class RecordPaymentRequest(BaseModel):
    relationship_id: UUID
    person_id: UUID
    amount: float = Field(gt=0)
    currency: str = Field(default="NGN", min_length=3, max_length=8)
    due_date: datetime

class UpdatePaymentStatusRequest(BaseModel):
    status: str = Field(pattern="^(pending|paid|late|defaulted)$")
    paid_date: datetime | None = None

class PaymentResponse(BaseModel):
    id: UUID
    relationship_id: UUID
    person_id: UUID
    amount: float
    currency: str
    due_date: datetime
    paid_date: datetime | None
    status: str

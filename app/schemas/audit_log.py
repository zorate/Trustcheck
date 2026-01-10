from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class AuditLogResponse(BaseModel):
    id: UUID
    business_id: UUID | None
    user_id: UUID | None
    action: str
    path: str
    method: str
    ip: str | None
    created_at: datetime
    details: dict | None

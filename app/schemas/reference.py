from pydantic import BaseModel, Field
from uuid import UUID

class ReferenceRequest(BaseModel):
    person_id: UUID
    level: int = Field(ge=0, le=2)
    source: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=1024)

class ReferenceResponse(BaseModel):
    id: UUID
    person_id: UUID
    level: int
    source: str | None
    notes: str | None

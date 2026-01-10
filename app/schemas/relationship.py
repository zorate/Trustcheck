from pydantic import BaseModel, Field
from uuid import UUID

class RelationshipCreate(BaseModel):
    person_id: UUID
    started_on: str = Field(min_length=10, max_length=10, pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    status: str = Field(default="active", pattern="^(active|inactive)$")

class RelationshipUpdate(BaseModel):
    status: str = Field(pattern="^(active|inactive)$")

class RelationshipOut(BaseModel):
    id: UUID
    business_id: UUID
    person_id: UUID
    started_on: str
    status: str

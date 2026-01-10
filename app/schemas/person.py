from pydantic import BaseModel, Field
from uuid import UUID

class AddPersonRequest(BaseModel):
    phone: str = Field(min_length=7, max_length=32)
    first_name: str | None = Field(default=None, max_length=128)
    last_name: str | None = Field(default=None, max_length=128)
    notes: str | None = Field(default=None, max_length=1024)

class UpdatePersonRequest(BaseModel):
    first_name: str | None = Field(default=None, max_length=128)
    last_name: str | None = Field(default=None, max_length=128)
    notes: str | None = Field(default=None, max_length=1024)

class PersonResponse(BaseModel):
    id: UUID
    first_name: str | None
    last_name: str | None

class RelationshipRequest(BaseModel):
    person_id: UUID
    started_on: str = Field(min_length=10, max_length=10)  # YYYY-MM-DD
    status: str = Field(default="active", pattern="^(active|inactive)$")

class RelationshipResponse(BaseModel):
    id: UUID
    person_id: UUID
    started_on: str
    status: str

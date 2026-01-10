from pydantic import BaseModel, Field, EmailStr
from uuid import UUID

class BusinessResponse(BaseModel):
    id: UUID
    name: str
    country: str
    phone: str | None
    email: EmailStr | None

class CreateStaffRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    is_admin: bool = False

class StaffResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    phone: str | None
    is_admin: bool
    is_active: bool

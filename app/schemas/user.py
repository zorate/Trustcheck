from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    is_admin: bool = False

class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    is_active: bool | None = None

class UserOut(BaseModel):
    id: UUID
    business_id: UUID
    full_name: str
    email: EmailStr
    phone: str | None
    is_admin: bool
    is_active: bool

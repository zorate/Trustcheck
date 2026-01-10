from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

class RegisterBusinessRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    country: str = Field(default="Nigeria", min_length=2, max_length=64)
    admin_full_name: str = Field(min_length=2, max_length=255)
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=255)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class RefreshRequest(BaseModel):
    refresh_token: str

class MeResponse(BaseModel):
    id: UUID
    business_id: UUID
    email: EmailStr
    full_name: str
    is_admin: bool

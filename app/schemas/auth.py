import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class BusinessRegisterRequest(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=200)
    business_type: str = Field(..., description="sme | landlord | cooperative | vendor")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)

    @field_validator("business_type")
    @classmethod
    def validate_business_type(cls, v: str) -> str:
        allowed = {"sme", "landlord", "cooperative", "vendor"}
        if v not in allowed:
            raise ValueError(f"business_type must be one of: {', '.join(allowed)}")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class BusinessUserOut(BaseModel):
    id: str
    business_id: str
    email: str
    full_name: str
    role: str
    is_active: bool


class AuthResponse(BaseModel):
    user: BusinessUserOut
    tokens: TokenResponse
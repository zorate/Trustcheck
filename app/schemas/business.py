from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class BusinessOut(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    business_type: str
    is_active: bool
    created_at: datetime


class CreateStaffRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=200)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field("staff", description="admin | staff")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"admin", "staff"}
        if v not in allowed:
            raise ValueError(f"role must be one of: {', '.join(allowed)}")
        return v


class StaffOut(BaseModel):
    id: str
    business_id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class UpdateStaffRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    role: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"admin", "staff"}
            if v not in allowed:
                raise ValueError(f"role must be one of: {', '.join(allowed)}")
        return v
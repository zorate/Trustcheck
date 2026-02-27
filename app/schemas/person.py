import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class AddPersonRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: str = Field(..., description="Any format — will be normalised and hashed")
    capacity_level: str = Field("none", description="none | basic | verified")
    notes: Optional[str] = Field(None, max_length=1000)
    relationship_type: str = Field(..., description="customer | tenant | member | vendor_client")
    relationship_start: datetime

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) < 7 or len(digits) > 15:
            raise ValueError("Phone number must be between 7 and 15 digits")
        return v

    @field_validator("capacity_level")
    @classmethod
    def validate_capacity(cls, v: str) -> str:
        allowed = {"none", "basic", "verified"}
        if v not in allowed:
            raise ValueError(f"capacity_level must be one of: {', '.join(allowed)}")
        return v

    @field_validator("relationship_type")
    @classmethod
    def validate_rel_type(cls, v: str) -> str:
        allowed = {"customer", "tenant", "member", "vendor_client"}
        if v not in allowed:
            raise ValueError(f"relationship_type must be one of: {', '.join(allowed)}")
        return v


class UpdatePersonRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    capacity_level: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("capacity_level")
    @classmethod
    def validate_capacity(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"none", "basic", "verified"}
            if v not in allowed:
                raise ValueError(f"capacity_level must be one of: {', '.join(allowed)}")
        return v


class PersonOut(BaseModel):
    id: str
    business_id: str
    phone_display: str
    full_name: str
    capacity_level: str
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PersonWithScoreOut(BaseModel):
    person: PersonOut
    risk_band: str
    recommendation: str
    total_score: Optional[int] = None
    cold_start: bool
    computed_at: Optional[datetime] = None
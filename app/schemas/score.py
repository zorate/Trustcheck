from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ScoreBreakdownOut(BaseModel):
    payment_history_score: int
    payment_history_max: int = 40
    payment_history_label: str
    consistency_score: int
    consistency_max: int = 20
    consistency_label: str
    duration_score: int
    duration_max: int = 15
    duration_label: str
    capacity_score: int
    capacity_max: int = 15
    capacity_label: str
    reference_score: int
    reference_max: int = 10
    reference_label: str
    total_score: int
    risk_band: str
    recommendation: str
    cold_start: bool
    payment_count: int
    computed_at: datetime


class ScoreSummaryOut(BaseModel):
    person_id: str
    total_score: int #added this 16/04/2026
    risk_band: str
    recommendation: str
    cold_start: bool
    computed_at: Optional[datetime] = None


class ComputeScoreResponse(BaseModel):
    person_id: str
    total_score: int
    risk_band: str
    recommendation: str
    cold_start: bool
    computed_at: datetime


class AddReferenceRequest(BaseModel):
    person_id: str
    reference_type: str = Field(..., description="informal | guarantor | member")
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("reference_type")
    @classmethod
    def validate_ref_type(cls, v: str) -> str:
        allowed = {"informal", "guarantor", "member"}
        if v not in allowed:
            raise ValueError(f"reference_type must be one of: {', '.join(allowed)}")
        return v


class ReferenceOut(BaseModel):
    id: str
    business_id: str
    person_id: str
    reference_type: str
    description: Optional[str] = None
    given_by: str
    is_active: bool
    created_at: datetime


class AuditLogOut(BaseModel):
    id: str
    business_id: Optional[str] = None
    actor_id: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

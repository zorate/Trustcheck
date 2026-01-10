from pydantic import BaseModel
from uuid import UUID

class ComputeScoreRequest(BaseModel):
    person_id: UUID

class TrustScoreResponse(BaseModel):
    id: UUID
    person_id: UUID
    score: int
    risk_band: str
    recommendation: str
    breakdown: dict

class TrustSummaryResponse(BaseModel):
    person_id: UUID
    score: int
    risk_band: str
    recommendation: str

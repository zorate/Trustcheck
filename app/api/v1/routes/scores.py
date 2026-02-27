from typing import Optional
from fastapi import APIRouter, Depends, Request
from app.api.deps import CurrentUser, get_client_ip, get_current_user, require_role
from app.schemas.common import APIResponse
from app.schemas.score import (AddReferenceRequest, ComputeScoreResponse,
                                ReferenceOut, ScoreBreakdownOut, ScoreSummaryOut)
from app.services import scoring_service

router = APIRouter(prefix="/scores", tags=["Trust Scores"])


@router.post("/compute/{person_id}", response_model=APIResponse[ComputeScoreResponse])
async def compute_score(person_id: str, request: Request,
                        current_user: CurrentUser = Depends(require_role("staff")),
                        ip: Optional[str] = Depends(get_client_ip)):
    result = await scoring_service.compute_and_store_score(person_id, current_user.business_id,
                                                           current_user.user_id, ip=ip)
    return APIResponse(data=result)


@router.get("/{person_id}", response_model=APIResponse[ScoreSummaryOut])
async def get_score(person_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return APIResponse(data=await scoring_service.get_score_summary(person_id,
                                                                     current_user.business_id))


@router.get("/{person_id}/breakdown", response_model=APIResponse[ScoreBreakdownOut])
async def get_score_breakdown(person_id: str,
                              current_user: CurrentUser = Depends(require_role("admin"))):
    return APIResponse(data=await scoring_service.get_score_breakdown(person_id,
                                                                       current_user.business_id))


@router.post("/references", response_model=APIResponse[ReferenceOut], status_code=201)
async def add_reference(body: AddReferenceRequest, request: Request,
                        current_user: CurrentUser = Depends(require_role("staff")),
                        ip: Optional[str] = Depends(get_client_ip)):
    ref = await scoring_service.add_reference(body, current_user.business_id,
                                              current_user.user_id, ip=ip)
    return APIResponse(data=ref, message="Reference added")


@router.delete("/references/{reference_id}", response_model=APIResponse[None])
async def revoke_reference(reference_id: str, request: Request,
                           current_user: CurrentUser = Depends(require_role("admin")),
                           ip: Optional[str] = Depends(get_client_ip)):
    await scoring_service.revoke_reference(reference_id, current_user.business_id,
                                           current_user.user_id, ip=ip)
    return APIResponse(message="Reference revoked")
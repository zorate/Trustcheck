from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.schemas.trust_score import ComputeScoreRequest, TrustScoreResponse, TrustSummaryResponse
from app.models.trust_score import TrustScore
from app.middleware.auth import get_current_user
from app.services.scoring import compute_trust_score

router = APIRouter(prefix="/api/v1/scoring", tags=["scoring"])

@router.post("/compute", response_model=TrustScoreResponse)
async def compute(payload: ComputeScoreRequest, request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    user = await get_current_user(request)
    ts = await compute_trust_score(db, user["bid"], payload.person_id)
    await db.commit()
    return TrustScoreResponse(
        id=ts.id,
        person_id=ts.person_id,
        score=ts.score,
        risk_band=ts.risk_band,
        recommendation=ts.recommendation,
        breakdown=ts.breakdown,
    )

@router.get("/summary/{person_id}", response_model=TrustSummaryResponse)
async def summary(person_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    user = await get_current_user(request)
    q = select(TrustScore).where(TrustScore.business_id == user["bid"], TrustScore.person_id == person_id, TrustScore.deleted == False)
    ts = (await db.execute(q)).scalars().first()
    if not ts:
        # compute on demand
        ts = await compute_trust_score(db, user["bid"], person_id)
        await db.commit()
    return TrustSummaryResponse(person_id=ts.person_id, score=ts.score, risk_band=ts.risk_band, recommendation=ts.recommendation)

@router.get("/explain/{person_id}", response_model=TrustScoreResponse)
async def explain(person_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request)
    user = await get_current_user(request)
    q = select(TrustScore).where(TrustScore.business_id == user["bid"], TrustScore.person_id == person_id, TrustScore.deleted == False)
    ts = (await db.execute(q)).scalars().first()
    if not ts:
        ts = await compute_trust_score(db, user["bid"], person_id)
        await db.commit()
    return TrustScoreResponse(
        id=ts.id,
        person_id=ts.person_id,
        score=ts.score,
        risk_band=ts.risk_band,
        recommendation=ts.recommendation,
        breakdown=ts.breakdown,
    )

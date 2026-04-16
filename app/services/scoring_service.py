import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.models.payment_record import PaymentRecord
from app.models.person import Person
from app.models.reference import Reference
from app.models.relationship import Relationship
from app.models.trust_score import TrustScore
from app.schemas.score import (
    ComputeScoreResponse,
    ScoreBreakdownOut,
    ScoreSummaryOut,
    AddReferenceRequest,
    ReferenceOut,
)
from app.services.audit_service import write_audit
from app.services.scoring_engine import (
    PaymentSummary,
    ScoreInputs,
    compute_score,
)

logger = logging.getLogger(__name__)


async def compute_and_store_score(
    person_id: str,
    business_id: str,
    actor_id: str,
    ip: Optional[str] = None,
) -> ComputeScoreResponse:
    """
    Gather all signal data for a person, run the scoring engine,
    and persist the result. Called explicitly by the API or after
    payment mutations.

    All queries are scoped to business_id.
    """
    # 1. Validate person belongs to this business
    person = await Person.find_one(
        Person.id == person_id,
        Person.business_id == business_id,
        Person.deleted_at == None,  # noqa: E711
    )
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    # 2. Gather payment records
    payments = await PaymentRecord.find(
        PaymentRecord.business_id == business_id,
        PaymentRecord.person_id == person_id,
        PaymentRecord.deleted_at == None,  # noqa: E711
    ).to_list()

    paid_on_time = sum(
        1 for p in payments
        if p.status == "paid" and p.paid_date and p.paid_date <= p.due_date
    )
    paid_late = sum(
        1 for p in payments
        if p.status == "late"
        or (p.status == "paid" and p.paid_date and p.paid_date > p.due_date)
    )
    missed = sum(1 for p in payments if p.status == "missed")
    pending = sum(1 for p in payments if p.status == "pending")

    payment_summary = PaymentSummary(
        total=len(payments),
        paid_on_time=paid_on_time,
        paid_late=paid_late,
        missed=missed,
        pending=pending,
    )

    # 3. Earliest relationship start date
    relationships = await Relationship.find(
        Relationship.business_id == business_id,
        Relationship.person_id == person_id,
        Relationship.deleted_at == None,  # noqa: E711
    ).to_list()
    relationship_start = (
        min((r.relationship_start for r in relationships), default=None)
        if relationships else None
    )

    # 4. Best active reference
    best_ref = await _get_best_reference(person_id, business_id)

    # 5. Compute
    now = datetime.now(timezone.utc)
    inputs = ScoreInputs(
        payments=payment_summary,
        relationship_start=relationship_start,
        capacity_level=person.capacity_level,
        reference_type=best_ref,
        computed_at=now,
    )
    result = compute_score(inputs)

    # 6. Persist (upsert)
    existing = await TrustScore.find_one(
        TrustScore.business_id == business_id,
        TrustScore.person_id == person_id,
    )

    if existing:
        existing.payment_history_score = result.payment_history.score
        existing.consistency_score = result.consistency.score
        existing.duration_score = result.duration.score
        existing.capacity_score = result.capacity.score
        existing.reference_score = result.reference.score
        existing.total_score = result.total_score
        existing.risk_band = result.risk_band
        existing.recommendation = result.recommendation
        existing.cold_start = result.cold_start
        existing.payment_count = result.payment_count
        existing.computed_at = now
        existing.updated_at = now
        await existing.save()
    else:
        score_doc = TrustScore(
            business_id=business_id,
            person_id=person_id,
            payment_history_score=result.payment_history.score,
            consistency_score=result.consistency.score,
            duration_score=result.duration.score,
            capacity_score=result.capacity.score,
            reference_score=result.reference.score,
            total_score=result.total_score,
            risk_band=result.risk_band,
            recommendation=result.recommendation,
            cold_start=result.cold_start,
            payment_count=result.payment_count,
            computed_at=now,
        )
        await score_doc.insert()

    await write_audit(
        action="score.compute",
        business_id=business_id,
        actor_id=actor_id,
        resource_type="trust_score",
        resource_id=person_id,
        detail={
            "total_score": result.total_score,
            "risk_band": result.risk_band,
            "cold_start": result.cold_start,
        },
        ip_address=ip,
    )

    return ComputeScoreResponse(
        person_id=person_id,
        total_score=result.total_score,
        risk_band=result.risk_band,
        recommendation=result.recommendation,
        cold_start=result.cold_start,
        computed_at=now,
    )


async def get_score_summary(person_id: str, business_id: str) -> ScoreSummaryOut:
    """Return band + recommendation only (default exposure)."""
    score = await _get_score_scoped(person_id, business_id)
    return ScoreSummaryOut(
        person_id=person_id,
        total_score=score.total_score, #added this line 16/04/2026
        risk_band=score.risk_band,
        recommendation=score.recommendation,
        cold_start=score.cold_start,
        computed_at=score.computed_at,
    )


async def get_score_breakdown(person_id: str, business_id: str) -> ScoreBreakdownOut:
    """Return the full signal breakdown for explainability."""
    # Recompute signals fresh to rebuild labels
    person = await Person.find_one(
        Person.id == person_id,
        Person.business_id == business_id,
        Person.deleted_at == None,  # noqa: E711
    )
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    score = await _get_score_scoped(person_id, business_id)

    payments = await PaymentRecord.find(
        PaymentRecord.business_id == business_id,
        PaymentRecord.person_id == person_id,
        PaymentRecord.deleted_at == None,  # noqa: E711
    ).to_list()

    paid_on_time = sum(
        1 for p in payments
        if p.status == "paid" and p.paid_date and p.paid_date <= p.due_date
    )
    paid_late = sum(
        1 for p in payments
        if p.status == "late"
        or (p.status == "paid" and p.paid_date and p.paid_date > p.due_date)
    )
    missed = sum(1 for p in payments if p.status == "missed")
    pending = sum(1 for p in payments if p.status == "pending")

    payment_summary = PaymentSummary(
        total=len(payments),
        paid_on_time=paid_on_time,
        paid_late=paid_late,
        missed=missed,
        pending=pending,
    )

    relationships = await Relationship.find(
        Relationship.business_id == business_id,
        Relationship.person_id == person_id,
        Relationship.deleted_at == None,  # noqa: E711
    ).to_list()
    relationship_start = (
        min((r.relationship_start for r in relationships), default=None)
        if relationships else None
    )

    best_ref = await _get_best_reference(person_id, business_id)
    now = datetime.now(timezone.utc)

    inputs = ScoreInputs(
        payments=payment_summary,
        relationship_start=relationship_start,
        capacity_level=person.capacity_level,
        reference_type=best_ref,
        computed_at=now,
    )
    result = compute_score(inputs)

    return ScoreBreakdownOut(
        payment_history_score=result.payment_history.score,
        payment_history_label=result.payment_history.label,
        consistency_score=result.consistency.score,
        consistency_label=result.consistency.label,
        duration_score=result.duration.score,
        duration_label=result.duration.label,
        capacity_score=result.capacity.score,
        capacity_label=result.capacity.label,
        reference_score=result.reference.score,
        reference_label=result.reference.label,
        total_score=result.total_score,
        risk_band=result.risk_band,
        recommendation=result.recommendation,
        cold_start=result.cold_start,
        payment_count=result.payment_count,
        computed_at=now,
    )


async def add_reference(
    req: AddReferenceRequest,
    business_id: str,
    actor_id: str,
    ip: Optional[str] = None,
) -> ReferenceOut:
    """Add an endorsement for a person — scoped to this business."""
    person = await Person.find_one(
        Person.id == req.person_id,
        Person.business_id == business_id,
        Person.deleted_at == None,  # noqa: E711
    )
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    ref = Reference(
        business_id=business_id,
        person_id=req.person_id,
        reference_type=req.reference_type,
        description=req.description,
        given_by=actor_id,
    )
    await ref.insert()

    await write_audit(
        action="reference.create",
        business_id=business_id,
        actor_id=actor_id,
        resource_type="reference",
        resource_id=ref.id,
        detail={"reference_type": req.reference_type},
        ip_address=ip,
    )

    return _ref_out(ref)


async def revoke_reference(
    reference_id: str,
    business_id: str,
    actor_id: str,
    ip: Optional[str] = None,
) -> None:
    """Revoke an endorsement."""
    ref = await Reference.find_one(
        Reference.id == reference_id,
        Reference.business_id == business_id,
        Reference.deleted_at == None,  # noqa: E711
    )
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference not found")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    ref.is_active = False
    ref.deleted_at = now
    ref.updated_at = now
    await ref.save()

    await write_audit(
        action="reference.revoke",
        business_id=business_id,
        actor_id=actor_id,
        resource_type="reference",
        resource_id=reference_id,
        ip_address=ip,
    )


async def _get_best_reference(person_id: str, business_id: str) -> str:
    """
    Return the highest-weight active reference type for a person.

    Priority: guarantor = member > informal > none
    """
    refs = await Reference.find(
        Reference.business_id == business_id,
        Reference.person_id == person_id,
        Reference.is_active == True,
        Reference.deleted_at == None,  # noqa: E711
    ).to_list()

    if not refs:
        return "none"

    ref_types = {r.reference_type for r in refs}

    if "guarantor" in ref_types or "member" in ref_types:
        return "guarantor"  # or member — both score 10 pts
    if "informal" in ref_types:
        return "informal"
    return "none"


async def _get_score_scoped(person_id: str, business_id: str) -> TrustScore:
    score = await TrustScore.find_one(
        TrustScore.business_id == business_id,
        TrustScore.person_id == person_id,
    )
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No score found — call POST /scores/compute first",
        )
    return score


def _ref_out(r: Reference) -> ReferenceOut:
    return ReferenceOut(
        id=r.id,
        business_id=r.business_id,
        person_id=r.person_id,
        reference_type=r.reference_type,
        description=r.description,
        given_by=r.given_by,
        is_active=r.is_active,
        created_at=r.created_at,
    )

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from app.models.payment import PaymentRecord, PaymentStatus
from app.models.relationship import Relationship
from app.models.reference import Reference
from app.models.trust_score import TrustScore

def _risk_band(score: int) -> tuple[str, str]:
    if 0 <= score <= 39:
        return ("High Risk", "Do not extend credit")
    if 40 <= score <= 59:
        return ("Medium Risk", "Limit exposure")
    if 60 <= score <= 79:
        return ("Low Risk", "Reasonable")
    return ("Very Low Risk", "Safe")

async def compute_trust_score(session: AsyncSession, business_id, person_id) -> TrustScore:
    # Signal 1: Payment History (40)
    q = select(PaymentRecord).where(
        PaymentRecord.business_id == business_id,
        PaymentRecord.person_id == person_id,
        PaymentRecord.deleted == False,
    )
    payments = (await session.execute(q)).scalars().all()
    if len(payments) == 0:
        s1 = 15
        history_label = "No history"
    else:
        late_count = sum(1 for p in payments if p.status in (PaymentStatus.late, PaymentStatus.defaulted))
        ontime_count = sum(1 for p in payments if p.status == PaymentStatus.paid and p.paid_date and p.due_date and p.paid_date <= p.due_date)
        total_paid = sum(1 for p in payments if p.status in (PaymentStatus.paid, PaymentStatus.late))
        if late_count > 0 and ontime_count == 0:
            s1 = 25
            history_label = "Paid late before"
        elif ontime_count > 0 and late_count > 0:
            # mostly on time if ontime >= late
            s1 = 35 if ontime_count >= late_count else 25
            history_label = "Mostly on time" if ontime_count >= late_count else "Paid late before"
        elif total_paid > 0 and late_count == 0:
            s1 = 40
            history_label = "Always on time"
        else:
            s1 = 25
            history_label = "Paid late before"

    # Signal 2: Payment Consistency (20)
    # Consistency: number of months with at least one payment vs gaps
    if len(payments) == 0:
        s2 = 5
        consistency_label = "Irregular / skipped"
    else:
        months = set()
        for p in payments:
            dt = p.paid_date or p.due_date
            if dt:
                months.add((dt.year, dt.month))
        months_count = len(months)
        # Relationship duration months
        rel_q = select(Relationship).where(
            Relationship.business_id == business_id,
            Relationship.person_id == person_id,
            Relationship.deleted == False,
        )
        rel = (await session.execute(rel_q)).scalars().first()
        if rel:
            # parse started_on YYYY-MM-DD
            try:
                start = datetime.strptime(rel.started_on, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except Exception:
                start = datetime.now(timezone.utc)
            now = datetime.now(timezone.utc)
            duration_months = max(1, (now.year - start.year) * 12 + (now.month - start.month))
        else:
            duration_months = months_count
        gap_ratio = 1 - (months_count / max(1, duration_months))
        if gap_ratio > 0.5:
            s2 = 5
            consistency_label = "Irregular / skipped"
        elif gap_ratio > 0.2:
            s2 = 12
            consistency_label = "Some gaps"
        else:
            s2 = 20
            consistency_label = "Consistent"

    # Signal 3: Relationship Duration (15)
    if len(payments) == 0 and not rel:
        s3 = 5
        duration_label = "<1 month"
    else:
        if rel:
            try:
                start = datetime.strptime(rel.started_on, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except Exception:
                start = datetime.now(timezone.utc)
            now = datetime.now(timezone.utc)
            months = max(0, (now.year - start.year) * 12 + (now.month - start.month))
            if months < 1:
                s3 = 5
                duration_label = "<1 month"
            elif 1 <= months <= 6:
                s3 = 10
                duration_label = "1–6 months"
            else:
                s3 = 15
                duration_label = "6 months"
        else:
            s3 = 5
            duration_label = "<1 month"

    # Signal 4: Capacity Indicator (15)
    # Derived from presence of notes in relationship/person or average payment amount
    avg_amount = 0.0
    if payments:
        avg_amount = float(sum(float(p.amount) for p in payments) / len(payments))
    if avg_amount == 0.0:
        s4 = 5
        capacity_label = "None"
    elif avg_amount < 50000:  # heuristic within system-only data
        s4 = 10
        capacity_label = "Basic (job, trade, business)"
    else:
        s4 = 15
        capacity_label = "Stable / verified"

    # Signal 5: Reference / Endorsement (10)
    ref_q = select(Reference).where(
        Reference.business_id == business_id,
        Reference.person_id == person_id,
        Reference.deleted == False,
    )
    ref = (await session.execute(ref_q)).scalars().first()
    if not ref:
        s5 = 0
        ref_label = "None"
    else:
        if ref.level == 1:
            s5 = 5
            ref_label = "Informal"
        elif ref.level == 2:
            s5 = 10
            ref_label = "Trusted member / guarantor"
        else:
            s5 = 0
            ref_label = "None"

    total = s1 + s2 + s3 + s4 + s5
    band, rec = _risk_band(total)
    breakdown = {
        "Payment History (40)": {"label": history_label, "points": s1},
        "Payment Consistency (20)": {"label": consistency_label, "points": s2},
        "Relationship Duration (15)": {"label": duration_label, "points": s3},
        "Capacity Indicator (15)": {"label": capacity_label, "points": s4},
        "Reference / Endorsement (10)": {"label": ref_label, "points": s5},
        "Total": total,
    }

    # Upsert TrustScore
    existing_q = select(TrustScore).where(
        TrustScore.business_id == business_id,
        TrustScore.person_id == person_id,
        TrustScore.deleted == False,
    )
    existing = (await session.execute(existing_q)).scalars().first()
    if existing:
        existing.score = total
        existing.risk_band = band
        existing.recommendation = rec
        existing.breakdown = breakdown
        await session.flush()
        return existing
    else:
        ts = TrustScore(
            business_id=business_id,
            person_id=person_id,
            score=total,
            risk_band=band,
            recommendation=rec,
            breakdown=breakdown,
        )
        session.add(ts)
        await session.flush()
        return ts

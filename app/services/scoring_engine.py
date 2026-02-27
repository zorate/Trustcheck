"""
TrustCheck Scoring Engine
=========================

Implements the exact 5-signal, 100-point scoring schema.
This module is PURE LOGIC — no I/O, no side effects.
All database access happens in scoring_service.py.

Signals
-------
1. Payment History     (40 pts) — outcomes of past obligations
2. Payment Consistency (20 pts) — regularity of payment behaviour
3. Relationship Duration (15 pts) — length of transactional history
4. Capacity Indicator  (15 pts) — self-reported income/capacity
5. Reference/Endorsement (10 pts) — endorsements from the business

Risk Bands
----------
0-39   → High Risk    → Do not extend credit
40-59  → Medium Risk  → Limit exposure
60-79  → Low Risk     → Reasonable
80-100 → Very Low Risk → Safe

Cold Start
----------
When fewer than 1 completed payment record exists, the score defaults
to minimum signal values and cold_start=True is flagged.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import NamedTuple


# ── Data Inputs ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PaymentSummary:
    """Distilled payment statistics passed to the engine."""
    total: int           # total payment obligations recorded
    paid_on_time: int    # paid on or before due_date
    paid_late: int       # paid after due_date
    missed: int          # never paid / written off
    pending: int         # not yet due


@dataclass(frozen=True)
class ScoreInputs:
    """All inputs required to compute a trust score."""
    payments: PaymentSummary
    relationship_start: datetime | None   # earliest relationship start date
    capacity_level: str                   # none | basic | verified
    reference_type: str                   # none | informal | guarantor | member
    computed_at: datetime


# ── Score Result ──────────────────────────────────────────────────────────────

class SignalResult(NamedTuple):
    score: int
    label: str


@dataclass(frozen=True)
class ScoreResult:
    payment_history: SignalResult
    consistency: SignalResult
    duration: SignalResult
    capacity: SignalResult
    reference: SignalResult
    total_score: int
    risk_band: str
    recommendation: str
    cold_start: bool
    payment_count: int
    computed_at: datetime


# ── Signal Scorers ────────────────────────────────────────────────────────────

def _score_payment_history(p: PaymentSummary) -> SignalResult:
    """
    Signal 1: Payment History (max 40 pts)

    No history           → 15
    Paid late before     → 25
    Mostly on time       → 35
    Always on time       → 40
    """
    completed = p.paid_on_time + p.paid_late + p.missed

    if completed == 0:
        return SignalResult(15, "No payment history")

    if p.paid_on_time == 0 and p.paid_late == 0 and p.missed > 0:
        # All missed — treat as late rather than no history
        return SignalResult(15, "No successful payments")

    total_resolved = p.paid_on_time + p.paid_late + p.missed
    on_time_rate = p.paid_on_time / total_resolved if total_resolved > 0 else 0.0

    if on_time_rate == 1.0:
        return SignalResult(40, "Always on time")
    elif on_time_rate >= 0.75:
        return SignalResult(35, "Mostly on time")
    elif p.paid_late > 0 or p.paid_on_time > 0:
        return SignalResult(25, "Paid late before")
    else:
        return SignalResult(15, "No history")


def _score_consistency(p: PaymentSummary) -> SignalResult:
    """
    Signal 2: Payment Consistency (max 20 pts)

    Irregular / skipped → 5
    Some gaps           → 12
    Consistent          → 20

    Consistency measures how reliably the person engages with obligations.
    We derive it from the ratio of missed + very late to total resolved.
    """
    completed = p.paid_on_time + p.paid_late + p.missed

    if completed == 0:
        return SignalResult(5, "Irregular — no completed payments")

    miss_rate = p.missed / completed if completed > 0 else 0.0

    if miss_rate == 0.0 and p.paid_late == 0:
        return SignalResult(20, "Consistent")
    elif miss_rate <= 0.15:
        return SignalResult(12, "Some gaps")
    else:
        return SignalResult(5, "Irregular / skipped payments")


def _score_duration(relationship_start: datetime | None, computed_at: datetime) -> SignalResult:
    """
    Signal 3: Relationship Duration (max 15 pts)

    < 1 month  → 5
    1–6 months → 10
    > 6 months → 15
    """
    if relationship_start is None:
        return SignalResult(5, "No relationship history")

    # Ensure both are timezone-aware for comparison
    now = computed_at
    start = relationship_start
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    delta_days = (now - start).days
    months = delta_days / 30.44  # average days per month

    if months >= 6:
        return SignalResult(15, "6+ months relationship")
    elif months >= 1:
        return SignalResult(10, "1–6 months relationship")
    else:
        return SignalResult(5, "Less than 1 month")


def _score_capacity(capacity_level: str) -> SignalResult:
    """
    Signal 4: Capacity Indicator (max 15 pts)

    none     → 5   (no verifiable capacity)
    basic    → 10  (self-reported job, trade, or business)
    verified → 15  (confirmed by document or trusted reference)
    """
    mapping = {
        "none":     SignalResult(5,  "No capacity information"),
        "basic":    SignalResult(10, "Basic capacity (job, trade, or business)"),
        "verified": SignalResult(15, "Stable / verified capacity"),
    }
    return mapping.get(capacity_level, SignalResult(5, "No capacity information"))


def _score_reference(reference_type: str) -> SignalResult:
    """
    Signal 5: Reference / Endorsement (max 10 pts)

    none              → 0
    informal          → 5
    guarantor | member → 10
    """
    mapping = {
        "none":      SignalResult(0,  "No endorsement"),
        "informal":  SignalResult(5,  "Informal endorsement"),
        "guarantor": SignalResult(10, "Trusted guarantor"),
        "member":    SignalResult(10, "Verified member reference"),
    }
    return mapping.get(reference_type, SignalResult(0, "No endorsement"))


# ── Risk Band Classifier ──────────────────────────────────────────────────────

def _classify_risk(total: int) -> tuple[str, str]:
    """
    Map a total score to a risk band and recommendation.

    Returns (risk_band, recommendation)
    """
    if total >= 80:
        return "very_low_risk", "Safe to extend credit"
    elif total >= 60:
        return "low_risk", "Reasonable — proceed with standard caution"
    elif total >= 40:
        return "medium_risk", "Limit exposure — start small"
    else:
        return "high_risk", "Do not extend credit"


# ── Main Compute Function ─────────────────────────────────────────────────────

def compute_score(inputs: ScoreInputs) -> ScoreResult:
    """
    Compute the full trust score from the given inputs.

    This is a pure function: same inputs always produce the same output.
    It is deterministic and has no side effects.
    """
    completed = (
        inputs.payments.paid_on_time
        + inputs.payments.paid_late
        + inputs.payments.missed
    )
    cold_start = completed < 1

    if cold_start:
        # Minimum floor values for all signals when data is insufficient
        payment_history = SignalResult(15, "No payment history (cold start)")
        consistency    = SignalResult(5,  "No data (cold start)")
        duration       = _score_duration(inputs.relationship_start, inputs.computed_at)
        capacity       = _score_capacity(inputs.capacity_level)
        reference      = _score_reference(inputs.reference_type)
    else:
        payment_history = _score_payment_history(inputs.payments)
        consistency    = _score_consistency(inputs.payments)
        duration       = _score_duration(inputs.relationship_start, inputs.computed_at)
        capacity       = _score_capacity(inputs.capacity_level)
        reference      = _score_reference(inputs.reference_type)

    total = (
        payment_history.score
        + consistency.score
        + duration.score
        + capacity.score
        + reference.score
    )

    # Clamp to valid range
    total = max(0, min(100, total))

    risk_band, recommendation = _classify_risk(total)

    return ScoreResult(
        payment_history=payment_history,
        consistency=consistency,
        duration=duration,
        capacity=capacity,
        reference=reference,
        total_score=total,
        risk_band=risk_band,
        recommendation=recommendation,
        cold_start=cold_start,
        payment_count=inputs.payments.total,
        computed_at=inputs.computed_at,
    )
"""
Unit tests for the TrustCheck scoring engine.

These are pure unit tests — no database, no async, no fixtures.
The engine is a pure function: same inputs → same outputs.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.services.scoring_engine import (
    PaymentSummary,
    ScoreInputs,
    compute_score,
)


def _now():
    return datetime.now(timezone.utc)


def _inputs(
    paid_on_time=0,
    paid_late=0,
    missed=0,
    pending=0,
    months_ago=0,
    capacity="none",
    reference="none",
):
    total = paid_on_time + paid_late + missed + pending
    start = _now() - timedelta(days=int(months_ago * 30.44)) if months_ago else None
    return ScoreInputs(
        payments=PaymentSummary(
            total=total,
            paid_on_time=paid_on_time,
            paid_late=paid_late,
            missed=missed,
            pending=pending,
        ),
        relationship_start=start,
        capacity_level=capacity,
        reference_type=reference,
        computed_at=_now(),
    )


class TestPaymentHistorySignal:
    def test_no_history_gives_15(self):
        result = compute_score(_inputs())
        assert result.payment_history.score == 15

    def test_all_on_time_gives_40(self):
        result = compute_score(_inputs(paid_on_time=5))
        assert result.payment_history.score == 40

    def test_mostly_on_time_gives_35(self):
        # 75%+ on time
        result = compute_score(_inputs(paid_on_time=3, paid_late=1))
        assert result.payment_history.score == 35

    def test_some_late_gives_25(self):
        # Below 75% on time
        result = compute_score(_inputs(paid_on_time=1, paid_late=3))
        assert result.payment_history.score == 25

    def test_cold_start_gives_15(self):
        result = compute_score(_inputs(pending=5))
        assert result.cold_start is True
        assert result.payment_history.score == 15


class TestConsistencySignal:
    def test_no_data_gives_5(self):
        result = compute_score(_inputs())
        assert result.consistency.score == 5

    def test_zero_misses_zero_late_gives_20(self):
        result = compute_score(_inputs(paid_on_time=10))
        assert result.consistency.score == 20

    def test_low_miss_rate_gives_12(self):
        # 10% miss rate — some gaps
        result = compute_score(_inputs(paid_on_time=9, missed=1))
        assert result.consistency.score == 12

    def test_high_miss_rate_gives_5(self):
        # 50% miss rate
        result = compute_score(_inputs(paid_on_time=1, missed=1))
        assert result.consistency.score == 5


class TestDurationSignal:
    def test_no_relationship_gives_5(self):
        result = compute_score(_inputs(paid_on_time=1))
        assert result.duration.score == 5

    def test_less_than_one_month_gives_5(self):
        result = compute_score(_inputs(paid_on_time=1, months_ago=0.5))
        assert result.duration.score == 5

    def test_two_months_gives_10(self):
        result = compute_score(_inputs(paid_on_time=1, months_ago=2))
        assert result.duration.score == 10

    def test_six_plus_months_gives_15(self):
        result = compute_score(_inputs(paid_on_time=1, months_ago=7))
        assert result.duration.score == 15


class TestCapacitySignal:
    def test_none_gives_5(self):
        result = compute_score(_inputs(paid_on_time=1, capacity="none"))
        assert result.capacity.score == 5

    def test_basic_gives_10(self):
        result = compute_score(_inputs(paid_on_time=1, capacity="basic"))
        assert result.capacity.score == 10

    def test_verified_gives_15(self):
        result = compute_score(_inputs(paid_on_time=1, capacity="verified"))
        assert result.capacity.score == 15


class TestReferenceSignal:
    def test_none_gives_0(self):
        result = compute_score(_inputs(paid_on_time=1, reference="none"))
        assert result.reference.score == 0

    def test_informal_gives_5(self):
        result = compute_score(_inputs(paid_on_time=1, reference="informal"))
        assert result.reference.score == 5

    def test_guarantor_gives_10(self):
        result = compute_score(_inputs(paid_on_time=1, reference="guarantor"))
        assert result.reference.score == 10

    def test_member_gives_10(self):
        result = compute_score(_inputs(paid_on_time=1, reference="member"))
        assert result.reference.score == 10


class TestRiskBands:
    def test_cold_start_is_high_risk(self):
        result = compute_score(_inputs())
        assert result.risk_band == "high_risk"

    def test_perfect_score_is_very_low_risk(self):
        result = compute_score(
            _inputs(
                paid_on_time=20,
                months_ago=8,
                capacity="verified",
                reference="guarantor",
            )
        )
        assert result.total_score == 100
        assert result.risk_band == "very_low_risk"

    def test_medium_risk_band(self):
        # Build a score in 40-59 range
        result = compute_score(_inputs(paid_on_time=1, paid_late=2, months_ago=2, capacity="none"))
        assert 40 <= result.total_score <= 59
        assert result.risk_band == "medium_risk"

    def test_score_does_not_exceed_100(self):
        result = compute_score(
            _inputs(
                paid_on_time=100,
                months_ago=24,
                capacity="verified",
                reference="guarantor",
            )
        )
        assert result.total_score <= 100

    def test_total_is_sum_of_signals(self):
        result = compute_score(
            _inputs(paid_on_time=5, months_ago=3, capacity="basic", reference="informal")
        )
        expected = (
            result.payment_history.score
            + result.consistency.score
            + result.duration.score
            + result.capacity.score
            + result.reference.score
        )
        assert result.total_score == expected


class TestColdStart:
    def test_only_pending_is_cold_start(self):
        result = compute_score(_inputs(pending=10))
        assert result.cold_start is True

    def test_one_resolved_payment_is_not_cold_start(self):
        result = compute_score(_inputs(paid_on_time=1))
        assert result.cold_start is False

    def test_cold_start_recommendation(self):
        result = compute_score(_inputs())
        assert "not" in result.recommendation.lower() or "do not" in result.recommendation.lower()
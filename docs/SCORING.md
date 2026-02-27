# TrustCheck Scoring Logic

## Overview

TrustCheck computes a **100-point trust score** from 5 behavioural signals. The score is:
- Based **only** on data entered by businesses and observed in the system
- Explainable — every point is traceable to a specific signal
- Deterministic — the same inputs always produce the same score
- A recommendation tool, not a decision tool

---

## Signal 1: Payment History (Max 40 points)

Measures the outcomes of past payment obligations.

| Condition | Points | Label |
|---|---|---|
| No completed payments | 15 | No payment history |
| At least one late payment | 25 | Paid late before |
| 75%+ paid on time | 35 | Mostly on time |
| 100% paid on time | 40 | Always on time |

**How on-time is determined:** A payment is on time if `paid_date ≤ due_date`. Late if `paid_date > due_date`. Missed if `status = missed`.

---

## Signal 2: Payment Consistency (Max 20 points)

Measures regularity — do they engage consistently with obligations?

| Condition | Points | Label |
|---|---|---|
| No completed payments | 5 | Irregular |
| Miss rate > 15% | 5 | Irregular / skipped |
| Miss rate ≤ 15% | 12 | Some gaps |
| Zero missed, zero late | 20 | Consistent |

**Miss rate** = missed / (paid_on_time + paid_late + missed)

---

## Signal 3: Relationship Duration (Max 15 points)

Measures how long the business has been transacting with the person.

| Duration | Points | Label |
|---|---|---|
| No relationship recorded | 5 | No history |
| Less than 1 month | 5 | Less than 1 month |
| 1 to 6 months | 10 | 1–6 months |
| More than 6 months | 15 | 6+ months |

**Start date:** The earliest `relationship_start` date across all relationships between this business and person.

---

## Signal 4: Capacity Indicator (Max 15 points)

Captures the person's known income/economic capacity. All values are self-reported by the business — no external data is pulled.

| Level | Points | Meaning |
|---|---|---|
| `none` | 5 | No capacity information provided |
| `basic` | 10 | Self-reported job, trade, or business |
| `verified` | 15 | Confirmed capacity (document or trusted reference) |

---

## Signal 5: Reference / Endorsement (Max 10 points)

Captures endorsements provided by the business.

| Type | Points | Meaning |
|---|---|---|
| `none` | 0 | No endorsement |
| `informal` | 5 | Verbal or informal vouching |
| `guarantor` | 10 | Formal guarantor arrangement |
| `member` | 10 | Verified cooperative member reference |

If multiple references exist, the highest-weight reference is used.

---

## Total Score and Risk Bands

```
total = signal_1 + signal_2 + signal_3 + signal_4 + signal_5
```

| Score | Risk Band | Recommendation |
|---|---|---|
| 80–100 | Very Low Risk | Safe to extend credit |
| 60–79 | Low Risk | Reasonable — proceed with standard caution |
| 40–59 | Medium Risk | Limit exposure — start small |
| 0–39 | High Risk | Do not extend credit |

---

## Cold Start

**Cold start** is flagged when a person has **zero completed payment records** (pending-only or no records).

During cold start:
- Payment History defaults to 15 (minimum)
- Consistency defaults to 5 (minimum)
- Duration, Capacity, and Reference still use actual values
- `cold_start: true` is included in all API responses
- The querying business is advised that the score lacks payment history

**Cold start is not a permanent state.** As soon as the first payment obligation is resolved (paid, late, or missed), the cold start flag is removed and full signal scoring begins.

---

## Score Evolution

Scores evolve as new payment records are added:

| Event | Expected change |
|---|---|
| First payment recorded as paid on time | Score increases |
| Consistent on-time payments over time | Score increases toward 100 |
| Missed payment recorded | Score decreases |
| Relationship reaches 6 months | Duration signal jumps to max |
| Capacity level upgraded from none → verified | +10 points |
| Trusted guarantor endorsement added | +10 points |

**Scores are recomputed on demand** by calling `POST /api/v1/scores/compute/{person_id}`.

---

## Worked Example

**Scenario:** A landlord queries a prospective tenant.

| Signal | Inputs | Score |
|---|---|---|
| Payment History | 4 paid on time, 1 paid late → 80% on time | 35 |
| Consistency | 0 missed, 1 late → miss rate = 0% | 12* |
| Duration | Relationship: 8 months | 15 |
| Capacity | Level: basic | 10 |
| Reference | One informal reference | 5 |
| **Total** | | **77** |

*Note: Consistency gives 12 because there is a late payment, even though miss rate is 0%. The late payment counts as a "gap".

**Result:** Low Risk — Reasonable. Proceed with standard caution.

---

## What This System Cannot Tell You

TrustCheck can only reflect behaviour **within your business's relationship** with this person. It cannot:
- Tell you about obligations at other businesses
- Access bank statements or transaction records
- Reflect formal credit history
- Predict future behaviour with certainty

Treat the score as one signal in your decision — not the only one.
# Scoring logic

## Total score: 100 points

### Signal 1: Payment History (40)
- No history → **15**
- Paid late before → **25**
- Mostly on time → **35**
- Always on time → **40**

### Signal 2: Payment Consistency (20)
- Irregular / skipped → **5**
- Some gaps → **12**
- Consistent → **20**

### Signal 3: Relationship Duration (15)
- <1 month → **5**
- 1–6 months → **10**
- 6 months → **15**

### Signal 4: Capacity Indicator (15)
- None → **5**
- Basic (job, trade, business) → **10**
- Stable / verified → **15**

### Signal 5: Reference / Endorsement (10)
- None → **0**
- Informal → **5**
- Trusted member / guarantor → **10**

## Risk bands
- 0–39 → **High Risk** → Do not extend credit
- 40–59 → **Medium Risk** → Limit exposure
- 60–79 → **Low Risk** → Reasonable
- 80–100 → **Very Low Risk** → Safe

## Implementation notes

- Uses only system-observed data: payments, relationships, references.
- Capacity indicator derived from average payment amount within the system.
- Consistency computed from months with payments vs relationship duration.
- Scores stored per business-person pair; recomputed on demand.

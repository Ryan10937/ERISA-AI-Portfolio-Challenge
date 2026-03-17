# Underpayment / Contract Rate Adjustment (CO-45 style)

**CARC CO-45 definition (summary):** charge exceeds fee schedule/maximum allowable or contracted/legislated fee arrangement.

## Challenge rule (fake contract)
Compute:
- `coverage_ratio = paid_amount / billed_amount`

If `coverage_ratio >= 0.70`, recommend **DO NOT PURSUE**.

If `< 0.70`, treat as potential underpayment workup.

## Suggested next steps for < 0.70
- Request contract terms / fee schedule (if available)
- Request line-level allowables and repricing details
- Summarize value: billed, paid, delta

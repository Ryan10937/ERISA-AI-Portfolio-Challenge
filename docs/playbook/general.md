# General Workup Guidelines (Challenge Corpus)

## Output structure
Your workup output must include:
- `missing_fields`
- `open_questions`
- `recommended_next_steps`
- `supporting_playbook_citations` (chunk_ids)

## Evidence and hallucinations
- Do not invent codes, dates, diagnoses, or contract terms.
- If information is missing, turn it into a question and a concrete request step.

## Confidence gating
When denial taxonomy confidence is low:
- Prefer producing an **information request plan** instead of a definitive recommendation.

## CO-45 special rule (challenge-specific)
For CO-45, compute:

`coverage_ratio = paid_amount / billed_amount`

If `coverage_ratio >= 0.70` (fake contract threshold for this challenge), recommend **DO NOT PURSUE**.

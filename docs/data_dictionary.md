# Data Dictionary

This challenge uses synthetic claims data (no PHI).

## data/claims.csv

Columns:
- claim_id (string): Unique identifier
- payer (string): Synthetic payer name
- plan_type (string): ERISA | NON_ERISA | empty
- denial_code (string): Example: CO-16, CO-29, CO-45, CO-50, CO-97, CO-27; may be empty
- denial_text (string): Free text denial description; may be empty or sparse
- days_since_denial (int): Age of denial in days; may be empty
- billed_amount (float): Total billed amount; may be empty
- paid_amount (float): Total paid amount; may be empty
- cpt_codes (string): Semicolon-delimited CPT/HCPCS-like codes; may be empty
- icd10_codes (string): Semicolon-delimited ICD-10-like codes; may be empty
- prior_appeals (int): Number of prior appeals; may be empty

Notes:
- CO-45 rows may have partial payment; your workup must compute `coverage_ratio` when billed and paid are present.
- CO-45 threshold (challenge rule): if `paid_amount / billed_amount >= 0.70`, recommend DO NOT PURSUE.

## data/denial_labels_train.csv
A labeled training set for the `predict_denial_taxonomy` tool.
Columns:
- denial_code
- denial_text
- label (one of: missing_info, timely_filing, underpayment, medical_necessity, coding_bundling, eligibility, other)

## data/playbook_chunks.jsonl
Pre-chunked retrieval corpus for the `retrieve_playbook` tool.
Each JSON line contains:
- chunk_id
- doc_id
- tags (list)
- text

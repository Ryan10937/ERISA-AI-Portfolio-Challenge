# ERISA Recovery — Denial Workup Agent Challenge Submission

## Summary
An agentic CLI that produces a structured workup for synthetic denied/underpaid claims.

## Deliverables

Submit:
1) Source code (git repo, can be your branch of this repository)
2) README with:
   - how to run
   - architecture summary
   - any tradeoffs
   - any indications that you put thought into this beyond leveraging code agents will be paramount for your application!
3) Example outputs for 3 claim_ids of your choice

---
## Usage
```console 
python scripts/main.py workup --claim-id CLAIM_ID --session-id SESSION_ID
or
python scripts/main.py ask --message "Explain your reasoning for those recommended next steps" --session-id SESSION_ID
```

## Artchetecture Summary
The agent does a claim denial analysis of a specified claim from the claims.csv provided. It utilizes a SQLite store and a session key to maintain persistence. The agent runs in two main modes: workup and ask. Both utilize the persistent session history, but have different output goals. The workup output uses a custom output schema class to ensure the model output conforms to the output schema provided in docs/workup_output_schema.json. The ask output is for human readable responses. The model chooses tools when appropriate: _predict_denial_taxonomy_tool, _retrieve_playbook_tool, _gather_ICD10_code_context, and _gather_CPT_code_context. The latter two tools are an innovative addition meant to give the model additional context by translating the ICD10 + CPT codes into meaningful text. This is particularly helpful when the denial reason is medically unnecessary.

---

## Innovations
1) Custom output schema class: strict adherance to the output schema causes a json conversion error about 25% of the time. To solve this, i allow the agent to retry up to 3 times. While this reduces the error rate from 25% to 1.5%, it is slow and more of a bandaid than a solution.
2) CPT and ICD10 code context: To implement these two context functions, local copies of code-explanation pairs are kept in the data folder. This adds a larger storage footprint to the agent's pipeline and has the potential to become outdated as these codes evolve over time. Given more time, it would be better to find a frequently updated website with these codes + explanations listed.  
3) Secondary agent call to get tags for playbook: While this adds extra time, the added resilience is a worthy trade.

## Example Output

### Example A
```console
python scripts/main.py workup --claim-id C-000009 --session-id Claim1
```
```json
✅ Result for C-000009:
{'claim_id': 'C-000009',
 'denial_taxonomy': {'category': 'submission/billing error',
                     'confidence': 0.25},
 'draft_narrative': 'The claim was denied for a submission/billing error. '
                    'Correcting demographics and adding an H&P will satisfy '
                    'the payer’s requirements. Since the claim was previously '
                    'appealed, the next step is to gather the missing data and '
                    'resubmit. The payout potential is high (approx. $16,552), '
                    'making a pursuit worthwhile.',
 'missing_fields': ['patient demographics', 'H&P documentation'],
 'open_questions': ['Is there updated demographic information available?',
                    'Can the H&P be obtained promptly?'],
 'payment_analysis': {'billed_amount': 16551.91,
                      'co45_contract_paid_gate': False,
                      'coverage_ratio': 0.0,
                      'paid_amount': 0.0},
 'pursuit_recommendation': 'pursue',
 'reasons': ['Denial due to submission/billing error; correcting patient '
             'demographics and adding required H&P documentation should '
             'resolve the issue. The claim has already been appealed once, so '
             'a resubmission is warranted.'],
 'recommended_next_steps': [{'citations': ['CO-16 denial guidelines'],
                             'detail': 'Ensure name, DOB, insurance ID, and '
                                       'address match payer records.',
                             'step': 'Obtain and verify accurate patient '
                                     'demographic information.'},
                            {'citations': ['CO-16 denial guidelines'],
                             'detail': 'The note should include a thorough '
                                       'history and physical examination '
                                       'relevant to the CPT codes 66984 '
                                       '(lipoaspiration) and 27130 (bypass).',
                             'step': 'Acquire and attach a complete H&P note.'},
                            {'citations': ['CO-16 denial guidelines'],
                             'detail': 'Use the payer’s electronic portal or '
                                       'fax as appropriate.',
                             'step': 'Resubmit claim with corrected '
                                     'information and attached '
                                     'documentation.'}],
 'supporting_playbook_citations': ['United Sample policy CO-16 resubmission '
                                   'instructions'],
 'trace': {'model_api': 'responses',
           'tools_called': [{'name': 'predict_denial_taxonomy',
                             'reason': 'initial classification'}]}}
```


### Example B
```console
python scripts/main.py workup --claim-id C-000076 --session-id Claim1
```
```json
✅ Result for C-000076:
{'claim_id': 'C-000076',
 'denial_taxonomy': {'category': 'bundled service denial', 'confidence': 0.41},
 'draft_narrative': 'The claim was denied because the services are considered '
                    'bundled under the payer’s policy. Since the claim has not '
                    'been appealed yet and the potential payment is around '
                    '$10,156, we recommend pursuing an appeal by reviewing the '
                    'bundle rules, gathering documentation that supports '
                    'separate medical necessity, and submitting a formal '
                    'appeal.',
 'missing_fields': [],
 'open_questions': [],
 'payment_analysis': {'billed_amount': 10156.19,
                      'co45_contract_paid_gate': False,
                      'coverage_ratio': 0.0,
                      'paid_amount': 0.0},
 'pursuit_recommendation': 'pursue',
 'reasons': ['Denial reason CO‑97 indicates that the billed services (99285 '
             'and 66984) are considered bundled under the payer’s policy. The '
             'claim has not yet been appealed and the billed amount is '
             'significant, making it worthwhile to review the bundle '
             'guidelines and submit a justified appeal.'],
 'recommended_next_steps': [{'citations': ['CO-97 bundle guidelines'],
                             'detail': 'Determine if the services are truly '
                                       'bundled or if separate claims can be '
                                       'justified based on distinct clinical '
                                       'necessity.',
                             'step': 'Review ACME Health bundled service '
                                     'policy for codes 99285 (ED visit) and '
                                     '66984 (lipoaspiration).'},
                            {'citations': ['ACME Health appeal instructions'],
                             'detail': 'Include a detailed note explaining the '
                                       'separate clinical contexts (e.g., '
                                       'acute ED encounter versus elective '
                                       'procedure) and any evidence of '
                                       'distinct medical necessity.',
                             'step': 'Prepare supporting documentation.'},
                            {'citations': ['CO-97 appeal process'],
                             'detail': 'Submit through the payer’s electronic '
                                       'portal, ensuring all required fields '
                                       'and attachments are included.',
                             'step': 'File an appeal with the required '
                                     'documentation and a clear justification '
                                     'for unbundling.'}],
 'supporting_playbook_citations': ['ACME Health policy CO-97 appeal '
                                   'guidelines'],
 'trace': {'model_api': 'responses',
           'tools_called': [{'name': 'predict_denial_taxonomy',
                             'reason': 'classify denial type'},
                            {'name': 'retrieve_playbook',
                             'reason': 'obtain policy guidance'}]}}
```


### Example C
```console
python scripts/main.py workup --claim-id C-000080 --session-id Claim1
```
```json
{'claim_id': 'C-000080',
 'denial_taxonomy': {'category': 'missing/incomplete information',
                     'confidence': 0.25},
 'draft_narrative': 'The claim was denied because the payer did not receive '
                    'adequate eligibility verification. This is a standard '
                    'procedural denial that can be resolved by obtaining the '
                    'required eligibility confirmation and resubmitting the '
                    'claim. Given the billed amount of ~$21,451 and the fact '
                    'that no prior appeals have been filed, pursuing a '
                    'resubmission is the appropriate action.',
 'missing_fields': ['eligibility verification'],
 'open_questions': ['Is an eligibility verification statement available for '
                    'the patient and service dates?',
                    'What method will be used to obtain the verification '
                    '(e.g., e‑claim, fax, portal)?'],
 'payment_analysis': {'billed_amount': 21450.58,
                      'co45_contract_paid_gate': False,
                      'coverage_ratio': 0.0,
                      'paid_amount': 0.0},
 'pursuit_recommendation': 'pursue',
 'reasons': ['Denial CO‑16 indicates that the claim was rejected due to '
             'missing or incomplete eligibility verification. The payer '
             'requires eligibility confirmation before proceeding, so the '
             'claim can be successfully resubmitted once this documentation is '
             'provided.'],
 'recommended_next_steps': [{'citations': ['Blue Example CO‑16 eligibility '
                                           'requirements'],
                             'detail': 'Contact the insurer’s eligibility '
                                       'portal or request the payer’s e‑claim '
                                       'response to confirm coverage for the '
                                       'dates and services billed.',
                             'step': 'Obtain eligibility verification for the '
                                     'patient.'},
                            {'citations': ['Blue Example CO‑16 submission '
                                           'guidelines'],
                             'detail': 'Include the verification as a PDF or '
                                       'electronic attachment in the same '
                                       'submission format required by Blue '
                                       'Example (e.g., e‑claim or fax).',
                             'step': 'Attach the verification to the claim.'},
                            {'citations': ['Blue Example CO‑16 resubmission '
                                           'instructions'],
                             'detail': 'Ensure all required fields (patient '
                                       'demographics, service dates, CPT and '
                                       'ICD‑10 codes) are accurate and that '
                                       'the eligibility verification is '
                                       'included.',
                             'step': 'Resubmit the claim with complete '
                                     'eligibility information.'}],
 'supporting_playbook_citations': ['Blue Example policy CO‑16 – '
                                   'missing/incomplete information guidelines',
                                   'Blue Example policy CO‑16 – eligibility '
                                   'verification process'],
 'trace': {'model_api': 'responses',
           'tools_called': [{'name': 'predict_denial_taxonomy',
                             'reason': 'classify denial type'},
                            {'name': 'retrieve_playbook',
                             'reason': 'obtain payer-specific guidance'}]}}
```

### Example D
```console
python scripts/main.py ask --message "In 2 sentences, summarize your pursuit recommendation for the previous 3 claims" --session-id Claim1
```
Pursue all three claims: for C‑000009 resubmit with correct demographics and an H&P note; for C‑000076 appeal by providing documentation that separates the bundled ED visit (99285) from the lipoaspiration (66984); for C‑000080 obtain and attach eligibility verification before resubmitting the claim. All three actions are warranted because each denial is procedural or bundle‑related, the billed amounts are substantial, and the claims have not yet been fully resolved.
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
Run with python scripts/main.py workup --claim-id CLAIM_ID --session-id SESSION_ID

## Artchetecture Summary
The agent does a claim denial analysis of a specified claim from the claims.csv provided. It utilizes a SQLite store and a session key to maintain persistence. The agent runs in two main modes: workup and ask. Both utilize the persistent session history, but have different output goals. The workup output uses a custom output schema class to ensure the model output conforms to the output schema provided in docs/workup_output_schema.json. The ask output is for human readable responses. The model chooses tools when appropriate: _predict_denial_taxonomy_tool, _retrieve_playbook_tool, _gather_ICD10_code_context, and _gather_CPT_code_context. The latter two tools are an innovative addition meant to give the model additional context by translating the ICD10 + CPT codes into meaningful text. This is particularly helpful when the denial reason is medically unnecessary.

---

Innovations
1) Custom output schema class: strict adherance to the output schema causes a json conversion error about 25% of the time. To solve this, i allow the agent to retry up to 3 times. While this reduces the error rate from 25% to 1.5%, it is slow and more of a bandaid than a solution.
2) CPT and ICD10 code context:
3) Secondary agent call to get tags for playbook: While this adds extra time, the 
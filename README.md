# ERISA Recovery — Denial Workup Agent Challenge

## Summary
Build a small agentic CLI that produces a structured workup for synthetic denied/underpaid claims.

This challenge evaluates:
- Autonomous tool calling (conditional tool selection + fallbacks)
- ML-as-a-tool (basic classifier wrapped as an Agents SDK *function tool*)
- Retrieval (RAG-lite) as a function tool with grounded citations
- Multi-turn state using SQLite-backed Sessions

No UI required.

---

## Non-negotiable tech requirements

### Required
- Python
- **OpenAI Agents SDK (Python)** (`pip install openai-agents`)
- **Responses API only** (Chat Completions is disallowed)
  - You must use the Agents SDK **OpenAI Responses model provider** (e.g., `OpenAIResponsesModel`)
- **Ollama** must be used via its OpenAI compatibility layer and **/v1/responses**
- Tools must be implemented as Agents SDK **function tools**
- Multi-turn memory must use Agents SDK **Sessions** with a SQLite-backed session store

### Automatic fail
- Any use of Chat Completions (direct or indirect)
- Calling Ollama via `/v1/chat/completions` instead of `/v1/responses`
- Tools not implemented via Agents SDK function tools
- No multi-turn persistence

---

## What you build

A CLI with at least these commands:

```bash
python -m workup_agent workup --claim-id C-CO45-001 --session-id demo_01
python -m workup_agent ask --session-id demo_01 --message "Why did you recommend that?"
```

- `workup` loads the claim row from `data/claims.csv` and outputs a single JSON object matching `docs/workup_output_schema.json`.
- `ask` continues the same conversation using the same session id (SQLite-backed), answering follow-up questions **without losing context**.

You may implement the CLI with `argparse`, `typer`, or any approach you prefer.

---

## Provided files

### Data
- `data/claims.csv` — inference dataset (contains missing values + edge cases)
- `data/denial_labels_train.csv` — labeled training data for your ML tool
- `data/playbook_chunks.jsonl` — retrieval corpus (pre-chunked)

### Docs
- `docs/data_dictionary.md`
- `docs/workup_output_schema.json`
- `docs/playbook/*.md` (human-readable source docs; retrieval should use `playbook_chunks.jsonl`)

---

## Required tools (exactly 2)

Implement both as Agents SDK function tools:

1) **ML classifier tool**
`predict_denial_taxonomy(denial_code: str | None, denial_text: str | None) -> DenialPrediction`

- Train from `data/denial_labels_train.csv`
- Must handle missing inputs and return `unknown` when appropriate
- Must return a `confidence` score and `top_features` (interpretability artifact)

2) **Retrieval tool**
`retrieve_playbook(query: str, category: str | None, denial_code: str | None, k: int = 5) -> list[PlaybookChunk]`

- Retrieve from `data/playbook_chunks.jsonl`
- Your final workup must cite `chunk_id`s used

---

## Autonomous tool calling requirements

Your agent must show at least **two distinct tool-call paths** across the dataset:

- **Path A:** ML → Retrieval → Workup (typical case)
- **Path B:** Retrieval → Workup (when ML is not applicable or low confidence)

Why this matters: the dataset includes missing/unknown values and OOD codes that require fallback behavior.

---

## Critical business rule: CO-45 contract-paid gate (challenge-specific)

Even though these are denials/underpayments, some should **not** be pursued based on how much was paid.

If `denial_code == "CO-45"` and:

`paid_amount / billed_amount >= 0.70`

then your output **must** set:

- `pursuit_recommendation = "do_not_pursue"`
- include a reason explaining the contract-paid threshold gate

If billed or paid is missing, you must output `pursuit_recommendation = "needs_info"` and list missing fields.

---

## Output contract

Your `workup` output must validate against:

- `docs/workup_output_schema.json`

At a high level, you must output:
- taxonomy + confidence
- payment analysis (including `coverage_ratio` and the CO-45 gate result)
- recommendation: pursue | do_not_pursue | needs_info
- missing fields + open questions
- next steps with citations
- trace: `model_api` must be `"responses"` and you must list tool calls you made

---

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

## Evaluation overview

We will run your CLI on scenarios including:
- missing denial codes
- missing ICDs or sparse denial text
- out-of-distribution denial codes
- contradictions (e.g., timely filing code with suspiciously low age)
- CO-45 threshold gate

We will also inspect for:
- Responses-only usage
- real tool-calling (not hard-coded outputs)

---

## References (for your convenience)
- Agents SDK docs: https://openai.github.io/openai-agents-python/
- Function tools: https://openai.github.io/openai-agents-python/tools/
- Sessions: https://openai.github.io/openai-agents-python/sessions/
- Ollama OpenAI compatibility (includes `/v1/responses` example): https://docs.ollama.com/api/openai-compatibility

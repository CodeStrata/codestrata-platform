# AI Experience Audit

> **ARCHIVE CANDIDATE (Phase 12.2.2)** — Retained for history. Do not treat as current public documentation. Prefer CHANGELOG / governance reports / public `docs/` for current guidance. File was **not deleted**.


**Phase:** 9.1 audit  
**Rule:** AI is a **capability**, not part of the product name (Governance branding).

## Where AI enters today

| Surface | Trigger | Optional? | Scope |
| ------- | ------- | --------- | ----- |
| Modernization Advisor | `codestrata assess --with-ai` | Yes (default `--no-ai`) | Community Engine |
| Advisor model | `--model-id` / env / `[ai].*` | Yes | Community |
| RAG embeddings / answers | Platform retrieval/answering + `codestrata repository` / MCP repo tools | Feature-flagged | Platform |
| CLI `codestrata ai` | providers/config/health | Meta | Platform extension |

Deterministic assessment **never requires** AI.

## Providers (advisor)

| Provider | Config | Notes |
| -------- | ------ | ----- |
| `bedrock` | Default `[ai].provider` | AWS credentials / region |
| `openai` | `[ai].provider = "openai"` | API key env |

Factory: `engine/src/codestrata/ai/providers/factory.py`.  
Profile `local` rejects `--with-ai`.

## Missing credentials / failures (verified)

Golden path: `--with-ai` without AWS creds + healthy defaults.toml:

- Assessment completes
- HTML/JSON written
- User-visible: `AI status: fallback (validated AI result not included)`
- Exit code `0`

Auth failures map to sanitized customer messaging; deterministic results retained  
(`application/assessment/service.py`, `reporting/ai_status.py`).

## Attribution

- HTML “Modernization Advisor” section only when enrichment succeeds
- Copy indicates AI interpretation is not merged into findings/recommendations
- JSON carries `ai_executed`, provider, model, status fields

## Token / cost visibility

Limited. Model ID shown on completion; no first-class customer cost meter in CLI summary. Token fields may appear in AI execution artifacts when present.

## Privacy

- Advisor sends assessment context to cloud provider when `--with-ai`
- Workspace/clone paths are local; Engine does not equal Platform retention
- User messaging that “source is not retained” needs clearer Community docs (gap P1)

## Community vs Platform AI

| Capability | Community | Platform |
| ---------- | --------- | -------- |
| Deterministic assess | Yes | Consumes via ingestion |
| Modernization Advisor | Yes (`--with-ai`) | N/A as Engine feature |
| Grounded repo/portfolio answering | No (Engine alone) | Yes (flags) |
| Provider CLI health (`ai` group) | Stub without Platform | Yes |

## Gaps to fix later

- Branding “CodeStrata AI” in HTML vs Governance “CodeStrata” (P1)
- `version` printing default Bedrock model for non-AI users (P2)
- Empty `answer_model` config trap (P0) — blocks assess even with `--no-ai` when settings revalidated mid-run
- Provider field hardcoding “bedrock” on some failure paths (P2 accuracy)

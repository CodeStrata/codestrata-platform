# Configuration Audit

> **ARCHIVE CANDIDATE (Phase 12.2.2)** — Retained for history. Do not treat as current public documentation. Prefer CHANGELOG / governance reports / public `docs/` for current guidance. File was **not deleted**.


**Phase:** 9.1 audit  
**Sources:** `engine/src/codestrata/config/settings.py`, defaults TOML, `.env.example`, Platform `ApiSettings`, feature-flag policies.

## Configuration surfaces

| Surface | Role | Scope |
| ------- | ---- | ----- |
| `codestrata.toml` | Primary Engine config | Community + local Platform bridges |
| Packaged `codestrata.defaults.toml` | Clean-install defaults | Community |
| `codestrata init` minimal TOML | First-run scaffold | Community |
| Env vars `CODESTRATA_*` | Overrides / secrets | Both |
| Profiles (`community`, `local`, `enterprise`, `bedrock`, `openai`) | Bundled defaults | Engine |
| Platform env (API key, DB URL, feature flags) | Commercial API | Platform |

## Precedence (Engine)

`--profile` > `CODESTRATA_PROFILE` > `codestrata.toml` > profile defaults  
(`codestrata config` help; `docs/configuration-profiles.md`)

## Notable Engine settings (customer-relevant)

| Area | Keys (illustrative) | Notes |
| ---- | ------------------- | ----- |
| Repository | `repository.path` / `url` / `branch` | Assess source |
| AI advisor | `ai.provider`, `ai.bedrock.*`, `ai.openai.*` | bedrock\|openai |
| Knowledge (Engine) | `knowledge.*`, embedding, vector_store | Local store; vector `memory`/`pgvector` |
| MCP | `mcp.enabled` | Default **false** |
| Static analysis | `static_analysis.*`, PMD | Optional |
| Agents | `agents.*` | Framework |
| Incremental | `incremental.*` | Opt-in |
| Platform publish | `platform_publishing.*` | Engine→Platform bridge |
| Report | `report.title`, sections | Defaults TOML title uses Engineering Assessment |

## Environment variables (high signal)

| Variable | Purpose |
| -------- | ------- |
| `CODESTRATA_PROFILE` | Profile selection |
| `CODESTRATA_BEDROCK_MODEL_ID` / region / AWS creds | Bedrock advisor |
| `CODESTRATA_OPENAI_*` / `OPENAI_API_KEY` | OpenAI advisor / answers |
| `CODESTRATA_PMD_PATH` | PMD binary |
| `CODESTRATA_DATABASE_URL` | Postgres (Platform + optional pgvector) |
| `CODESTRATA_PLATFORM_API_KEY` | Platform REST auth |
| `CODESTRATA_PLATFORM_TOKEN` | Publishing auth (Engine side) |
| `CODESTRATA_*_ENABLED` | Platform feature gates (EI, presentation, roadmap, answering, portfolio retrieval/answering, retrieval indexing) |
| Deprecated | `CODESTRATA_PLATFORM_DATABASE_URL`, `CODESTRATA_PGVECTOR_URL` |

## SQLite status

| Context | Status |
| ------- | ------ |
| Platform commercial DB | **Not supported** (URLs rejected) |
| Engine knowledge store | **Intentional** local SQLite (`knowledge.sqlite`) |
| Stale refs | Record for cleanup if any docs imply Platform SQLite (see RC notes in `database.py`) |

**This phase does not remove stale references.**

## Confirmed defect (P0)

`BedrockSettings.answer_model: str = ""` with validator that returns `None` for blank strings → type error when TOML sets `answer_model = ""` (monorepo `codestrata.toml`).  
**Evidence:** assess run aborted after “Resolving assessment activation” with Pydantic validation error; no reports written.  
**Path:** `engine/src/codestrata/config/settings.py` (`BedrockSettings`).

## Community vs Platform settings

| Community-useful | Platform-only / commercial |
| ---------------- | -------------------------- |
| repository, report, ai advisor, mcp, static_analysis, local knowledge | `CODESTRATA_DATABASE_URL` Postgres, API key, EI/presentation/roadmap/answering flags, multi-tenant persistence |

## Phase 9 config actions (planned only)

1. Fix blank `answer_model` coercion (P0).
2. Single operator reference for Platform flags.
3. Clearer Community-safe defaults (no empty-string traps).
4. Align `report.title` defaults with Engineering Assessment naming.
5. Document SQLite Engine-only clearly in user-facing config docs.

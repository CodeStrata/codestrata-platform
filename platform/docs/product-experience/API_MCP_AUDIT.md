# API and MCP Audit

> **ARCHIVE CANDIDATE (Phase 12.2.2)** — Retained for history. Do not treat as current public documentation. Prefer CHANGELOG / governance reports / public `docs/` for current guidance. File was **not deleted**.


**Phase:** 9.1 audit  
**Sources:** `platform/.../api/app.py`, controllers, `engine/.../interfaces/mcp/`, Platform MCP/CLI extensions.

## Platform REST (Commercial)

- Base: `/api/v1`
- Title: **CodeStrata Commercial Platform API**
- Auth: `CODESTRATA_PLATFORM_API_KEY` (Bearer); `/health` + `/ready` public
- Persistence: PostgreSQL only

### Route groups (tags)

Organizations, Workspaces, Repositories, Assessments, Assessment Intelligence, Engineering Intelligence, Ingestion (+ Artifacts, Intelligence), Knowledge Graphs (+ Intelligence), Retrieval, Answering, Portfolio, Portfolio Retrieval, Portfolio Answering, Executive Intelligence, Executive Presentation, Strategic Portfolio Roadmap, Health.

**Issue:** `openapi_tags` in `app.py` lists only a subset → OpenAPI UI incomplete (P1).

### Feature flags (default off)

| Flag | Surface |
| ---- | ------- |
| `CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED` | EI |
| `CODESTRATA_EXECUTIVE_PRESENTATION_ENABLED` | Presentation (on-read) |
| `CODESTRATA_STRATEGIC_ROADMAP_ENABLED` | Roadmap (on-read) |
| `CODESTRATA_ANSWERING_ENABLED` | Repo answering |
| `CODESTRATA_PORTFOLIO_*` | Portfolio retrieval/answering |
| `CODESTRATA_RETRIEVAL_INDEXING_ENABLED` | Indexing |

### Naming / boundary risks

- Internal terms (CEIM) appear as “Engineering Snapshot” in some summaries — keep customer language consistent with Knowledge.
- “Commercial Platform” vs product name **CodeStrata Platform**.

## MCP (Engine + extensions)

| Command | Behavior |
| ------- | -------- |
| `mcp serve` | Start FastMCP server |
| `mcp tools` | List tools (requires mcp enabled) |
| `mcp health` | Sanitized health |

Server display name: **CodeStrata** (`CODESSTRATA_MCP_NAME`).

**Community tools:** assessments, findings, recommendations, run_assessment, rules/evidence/architecture helpers, agents/incremental (as registered).

**Platform extension tools:** enterprise KG tools; `repository_search` / `repository_answer` / domain RAG helpers.

**Default config:** `[mcp].enabled=false` → tools command blocked (verified).

## Community availability

| Surface | Community alone |
| ------- | --------------- |
| Platform REST | No |
| Engine MCP (extra + enabled) | Yes |
| Platform MCP extensions | No |

## Phase 9 API/MCP actions (planned only)

1. Complete OpenAPI tags/descriptions. **Done in 9.5** — see [API_MCP_EXPERIENCE.md](API_MCP_EXPERIENCE.md).
2. Customer-facing naming pass (Platform vs Commercial vs Enterprise). **Done in 9.3/9.5**.
3. First-run MCP enablement guidance. **Done in 9.2/9.5**.
4. Document tool list split Community vs Platform. **Done in 9.5** — `engine/docs/mcp/tools.md`.
5. SDK readiness later (public API freeze). **Tracked in** [SDK_READINESS.md](SDK_READINESS.md).

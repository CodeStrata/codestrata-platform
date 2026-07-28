# SDK readiness (Phase 9.7)

> **ARCHIVE CANDIDATE (Phase 12.2.2)** — Retained for history. Do not treat as current public documentation. Prefer CHANGELOG / governance reports / public `docs/` for current guidance. File was **not deleted**.


**Status:** Ready for public contract consumption (SDKs not yet published)  
**Authority:** Complements
[`governance/playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md`](../../../governance/playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md)

## Verdict

Platform OpenAPI `/api/v1` and Engine CLI / MCP / `report.json` contracts are
**stable enough** for:

- CodeStrata VS Code / Cursor extensions (when implemented)
- MCP clients
- CLI automation
- Customer integrations
- Internal Platform services

Language SDKs may be **generated** from OpenAPI + these docs. Publishing packages
to PyPI/npm is **not** required for Phase 9.7 exit.

## Generation inputs

| Input | Location |
| ----- | -------- |
| OpenAPI | Platform `/openapi.json` (`info.version` = `v1`) |
| Error envelope | `ErrorResponseDto` in OpenAPI components |
| Auth | `PlatformApiKey` Bearer scheme |
| MCP catalogs | `engine/docs/mcp/tools.md` |
| Report schema | `engine/.../schemas/assessment/codestrata.io/v1.2/AssessmentReport.json` |
| Compatibility | Governance playbook above |

## Checklist

| Criterion | Status |
| --------- | ------ |
| Stable `/api/v1` resource hierarchy | Met |
| Uniform error envelope | Met (documented + OpenAPI component) |
| Bearer auth documented | Met |
| Pagination `PageMetaDto` / `PageResponseDto` | Met |
| Compatibility + deprecation policy | Met (Governance playbook) |
| Integration examples | Met ([INTEGRATION_EXAMPLES.md](INTEGRATION_EXAMPLES.md)) |
| Extension API needs identified | Met ([EXTENSION_READINESS.md](EXTENSION_READINESS.md)) |
| Community vs Platform MCP matrix | Met (`engine/docs/mcp/tools.md`) |
| OpenAPI request examples on golden-path ops | Met (org create + ask) |
| Per-operation feature-flag extensions (`x-codestrata-flag`) | Recommended (non-blocking) |
| Full DTO Field description coverage | Recommended (non-blocking) |
| OAuth / user identity | Out of scope (shared secret intentional) |

## Remaining recommendations (non-blocking)

1. Annotate feature-flagged operations with `x-codestrata-flag` in OpenAPI.
2. Prefer path-scoped ask helpers in generated SDKs; keep dual routes as aliases.
3. Normalize remaining OpenAPI summary casing in a polish pass.
4. Expand Field descriptions across all request/response DTOs.
5. SDK wrappers: distinct types for Engineering Snapshot vs Portfolio Snapshot.
6. Keep `enterprise_*` MCP names; expose display aliases in SDK docs.
7. Runtime capability discovery for MCP (already via `list_tools`) — document in each SDK README.
8. Add more OpenAPI `examples` for ingestion and knowledge-graph golden paths.
9. Publish changelog discipline in Community release notes for CLI/config.

## Explicit non-goals (still)

- Shipping `codestrata-python` / `codestrata-typescript` packages in this phase
- Renaming public REST paths
- Breaking `report.json` schema 1.2

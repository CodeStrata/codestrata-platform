# API & MCP Experience (Phase 9.5)

**Status:** Implemented (documentation + OpenAPI/MCP discoverability polish)  
**Audience:** Integrators and maintainers  
**Does not change:** Engineering Intelligence logic, assessment runtime, CEIM,
Knowledge Graph algorithms, Retrieval/Answering/Portfolio/Executive behavior,
or report generation.

## Product boundary

| Surface | Product | Typical use |
| ------- | ------- | ----------- |
| `codestrata assess` / local knowledge / Community MCP | **CodeStrata Engine** | Local Engineering Assessment |
| Platform REST `/api/v1` | **CodeStrata Platform** | Multi-user APIs |
| Platform MCP extensions (`repository_*`, `enterprise_*`) | **CodeStrata Platform** | Retrieval, Answering, Engineering Knowledge Graph |

AI is an optional Engine capability. Platform API keys are not AI provider credentials.

## Platform REST

- Base path: `/api/v1`
- OpenAPI: `/openapi.json`, `/docs`, `/redoc` (docs public only outside production when a key is configured)
- Auth: `Authorization: Bearer <key>` from `CODESTRATA_PLATFORM_API_KEY`
- Errors: `{"error":{"code","message","details?"}}`
- Version: URL prefix + OpenAPI `info.version` (`v1`)

Authoritative OpenAPI text lives in `codestrata_platform.api.app` (tags, description,
security scheme). Do not duplicate endpoint inventories here — use `/openapi.json`.

Feature flags (operator): answering, portfolio retrieval/answering, executive
intelligence/presentation, strategic roadmap, retrieval indexing. See
[CONFIGURATION_AUDIT.md](CONFIGURATION_AUDIT.md) and Platform settings env vars.

## Community Engine MCP

Enable `[mcp].enabled = true`, then:

```bash
codestrata mcp serve --config codestrata.toml
codestrata mcp tools --config codestrata.toml
```

Core tools include assessments, findings, recommendations, `run_assessment`,
rules/evidence/architecture helpers. Optional AI artifacts require Engine AI
provider configuration at assess time.

Docs hub: [engine/docs/mcp/README.md](../../../engine/docs/mcp/README.md).

## Platform MCP extensions

Registered when the Platform package is installed and extension entry points load:

- `repository_*` — Repository Retrieval / Answering (deterministic extractive answer)
- `enterprise_*` — Engineering Knowledge Graph

See [engine/docs/mcp/tools.md](../../../engine/docs/mcp/tools.md) and
[../knowledge_graph/mcp.md](../knowledge_graph/mcp.md).

## Examples

Community assessment (CLI, not Platform REST):

```bash
codestrata assess /path/to/repo --no-ai
codestrata assess /path/to/repo --with-ai   # needs Engine AI provider creds
```

Platform REST (illustrative):

```bash
curl -sS -H "Authorization: Bearer $CODESTRATA_PLATFORM_API_KEY" \
  "$PLATFORM_BASE/api/v1/organizations"
```

MCP Community:

```json
{"name": "run_assessment", "arguments": {"repository": ".", "with_ai": false}}
```

MCP Platform (when available):

```json
{
  "name": "repository_search",
  "arguments": {
    "query": "authentication",
    "tenant_id": "example-tenant",
    "repository_id": "example-repo"
  }
}
```

## Canonical authorities (do not duplicate)

- Governance: [`governance/`](../../../governance/)
- Knowledge: [`knowledge/`](../../../knowledge/)
- Design System: [`governance/assets/DESIGN-SYSTEM.md`](../../../governance/assets/DESIGN-SYSTEM.md)
- Community/Platform boundaries: [`governance/constitution/006_COMMUNITY_PLATFORM_BOUNDARIES.md`](../../../governance/constitution/006_COMMUNITY_PLATFORM_BOUNDARIES.md)

## Related

- [API_MCP_AUDIT.md](API_MCP_AUDIT.md) — Phase 9.1 baseline
- [SDK_READINESS.md](SDK_READINESS.md) — Phase 9.7 gaps

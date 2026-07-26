# CodeStrata MCP server

**Status:** Phase 2C knowledge-store tools + Phase 5.7 repository-intelligence tools.

See the Phase 5.7 guides:

- [docs/mcp/overview.md](mcp/overview.md)
- [docs/mcp/setup.md](mcp/setup.md)
- [docs/mcp/tools.md](mcp/tools.md)
- [docs/mcp/client-examples.md](mcp/client-examples.md)
- [docs/mcp/security.md](mcp/security.md)
- [docs/mcp/troubleshooting.md](mcp/troubleshooting.md)

## Architecture

```text
MCP client (Cursor, etc.)
        ↓
aimf mcp serve  (stdio | streamable-http)
        ↓
CodeStrata FastMCP tools / resources / prompts
        ↓
KnowledgeQueryService / RepositoryRetriever / GroundedAnswerEngine
        ↓
KnowledgeStore + VectorStore
```

MCP never executes SQL, opens blob files, or reads `report.json` / `report.html`
outside application ports.

## Start

```bash
# Enable [mcp].enabled = true in aimf.toml first
aimf mcp serve --config aimf.toml
aimf mcp tools --config aimf.toml
aimf mcp health --config aimf.toml
```

Transport defaults to **stdio**. HTTP (`--transport http`) binds to `127.0.0.1`
by default.

## Repository intelligence tools

Registered names use underscores (`repository_search`, `repository_answer`, …).
Dotted aliases (`repository.search`, …) are documented in
[mcp/overview.md](mcp/overview.md).

`repository_answer` uses **deterministic extractive** answering — not generative AI.

| `get_ai_execution` / `get_ai_enrichment` | Optional AI artifacts |
| `run_assessment` | Execute assessment + persist knowledge |

## Resources

- `codestrata://repositories`
- `codestrata://repositories/{repository_id}`
- `codestrata://repositories/{repository_id}/latest-assessment`
- `codestrata://assessments/{run_id}/findings`
- `codestrata://assessments/{run_id}/recommendations`

## Prompts

- `review_repository`
- `explain_modernization_plan`
- `review_snapshot_changes`

Prompts supply deterministic JSON context; the client model interprets. They do
not call Bedrock inside the MCP server.

## Limits

Collection tools return `{items, returned_count, truncated, limit}`.

Defaults/maxima match KnowledgeQueryService bounds (repositories 50/500,
assessments 20/200, findings 100/500, components 100/1000, dependency depth ≤ 3).

Full graphs, manifests, and HTML reports are not returned by general tools.

## Security / trust model

This server is a **local developer tool**.

- No authentication
- Not safe for untrusted public network exposure
- No arbitrary filesystem/SQL/shell tools
- Local path aliases omitted from public repository DTOs
- Credential-bearing URLs rejected by existing validators
- Errors sanitized (no stack traces, secrets, or sqlite details)

## Assessment execution

`run_assessment` calls `AssessmentApplicationService`, persists knowledge through
the existing store, and returns concise IDs + counts for follow-up query tools.

## Agent workflow tools (Phase 2E)

Five additive high-level tools call `AgentOrchestrator` (same application
services as granular tools):

| Tool | Workflow |
| ---- | -------- |
| `review_repository_with_agents` | Repository review |
| `assess_repository_with_agents` | Assess + validate |
| `validate_assessment_with_agents` | Validation |
| `compare_snapshots_with_agents` | Snapshot comparison |
| `review_modernization_with_agents` | Modernization review |

Granular tools remain for precise queries. Agent tools return bounded workflow
packages (status, IDs, summaries, steps, validation). Full evidence and HTML are
not returned. Blocking validation is a structured result.

Factory: `create_mcp_server(..., agent_orchestrator=optional)`. When omitted,
the factory composes an orchestrator from the shared query/assessment services.

CLI sibling: `aimf agent …` (see [agent-framework.md](agent-framework.md)).

## Incremental tools (Phase 2F.3)

Four additive tools (granular + agent tools unchanged):

| Tool | Purpose |
| ---- | ------- |
| `create_incremental_assessment_plan` | Plan only |
| `execute_incremental_assessment` | Opt-in execute + validate + provenance |
| `get_incremental_execution` | Load execution record |
| `explain_incremental_execution` | Bounded deterministic explanations |

Requires `[incremental].rollout_mode` of `plan_only` or `opt_in`. Default remains
`off`. CLI sibling: `aimf incremental …` (see
[incremental-assessment.md](incremental-assessment.md)).

## Phase 2 status

Phase 2 is complete for controlled opt-in incremental use. Full assessment remains
the default.

## Enterprise Knowledge Graph (Phase 3)

Additive YAML enterprise architecture tools (optional; disabled by default). See
[enterprise-knowledge-graph/README.md](enterprise-knowledge-graph/README.md).

MCP tools include workspace validate/build, graph/entity query, neighborhood,
dependency paths, repository context, finding/recommendation impact, explain,
and graph version compare. Read-only resources under
`codestrata://enterprise/...` are registered when the enterprise query service
is configured.

Analysis Intelligence remains Phase 4; GitHub PR review remains Phase 6.

## Next phase

See [../ROADMAP.md](../ROADMAP.md).

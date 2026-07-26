# MCP Tools

All repository-intelligence tools return a common envelope
(`mcp-tool-response` 1.0.0):

- `schema_name` / `schema_version`
- `request_id` (deterministic fingerprint)
- `tool_name`
- `status` — `success` | `partial` | `empty` | `insufficient_evidence` | `disabled` | `failed`
- `data`
- `coverage`
- `diagnostics`
- `limitations`
- `generated_at` — `"deterministic"` in this phase
- `fingerprint`

## repository_search

Delegates to `RepositoryRetriever`. Required: `query`, `tenant_id`, `repository_id`.
Omits embeddings and database information.

## repository_answer

Delegates to `GroundedAnswerEngine`. Label: **deterministic extractive** —
not generative AI / not production. Provider identity is included in `data.provider`
and `data.provider_notes`.

## repository_findings / repository_recommendations

Read Phase 3 findings/recommendations for the latest completed assessment of
`repository_id` via `KnowledgeQueryService`. No arbitrary report-file reads.

## repository_assessments

Assessment summaries and counts for a repository scope.

## repository_files

Indexed file knowledge only (vector/retrieval scope). No arbitrary filesystem access.

## Pack tools

`repository_architecture`, `repository_security`, `repository_dependencies`,
`repository_tests`, `repository_cloud`, `repository_ai_readiness`,
`repository_performance` — filter findings/recommendations by intelligence pack.

## repository_health

Sanitized dependency health: transport, retrieval/answer availability, vector-store
provider type, embedding/answer provider identity. Never credentials or URLs.

## Result bounding

When `max_result_characters` is exceeded, complete lower-priority collections are
omitted (never mid-JSON truncation), status becomes `partial`, and diagnostics
record exclusions.

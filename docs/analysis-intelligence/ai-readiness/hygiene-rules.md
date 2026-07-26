# AI Readiness Hygiene Rules

Phase **4.8.3** — `ai_readiness.core` @ **1.0.0**

Rules consume **only** in-memory `AggregatedRepositoryAiReadinessEvidence`.
They do not re-read repository files, execute AI/LLM calls, invent readiness
scores, or emit modernization recommendations.

Human aliases **AI-001** … **AI-061** map to machine IDs
`ai_readiness.ai-00N`.

## Configuration

```toml
[evidence.repository_ai_readiness]
enabled = true

[rules]
enabled = true

[rules.ai_readiness]
enabled = true
```

All gates default to **disabled**. Rules never trigger evidence collection.
Evidence may run without rules. Enabling `[rules.ai_readiness]` does **not**
enable `[analysis.ai_readiness]`. When analysis is on, Phase **4.8.4** projects
inventories over Findings (synthesis still deferred).

Per-rule toggles (default enabled when the pack is on):

```toml
[rules.ai_readiness.ai_001]
enabled = true
# … ai_002, ai_003, ai_010, ai_011, ai_020, ai_021, ai_022,
#   ai_030, ai_031, ai_032, ai_040, ai_041, ai_050, ai_051,
#   ai_060, ai_061
```

## Rule catalog

| Alias | Rule ID | Trigger | Severity | Category |
| ----- | ------- | ------- | -------- | -------- |
| AI-001 | `ai_readiness.ai-001` | ≥1 known API boundary kinds (REST/GraphQL/gRPC/controller/router/handler) | INFORMATIONAL | `ai_readiness.api_and_service_boundaries` |
| AI-002 | `ai_readiness.ai-002` | ≥1 OpenAPI facts | INFORMATIONAL | `ai_readiness.api_and_service_boundaries` |
| AI-003 | `ai_readiness.ai-003` | Usable evidence; zero AI-001 kinds and zero OpenAPI (suppressed when AI-001/002 match) | LOW | `ai_readiness.api_and_service_boundaries` |
| AI-010 | `ai_readiness.ai-010` | ≥1 architecture or ADR docs | INFORMATIONAL | `ai_readiness.documentation_and_metadata_quality` |
| AI-011 | `ai_readiness.ai-011` | Usable evidence; zero README/architecture/ADR/API docs (suppressed when supporting docs present) | LOW | `ai_readiness.documentation_and_metadata_quality` |
| AI-020 | `ai_readiness.ai-020` | ≥1 database repository facts | INFORMATIONAL | `ai_readiness.data_access_patterns` |
| AI-021 | `ai_readiness.ai-021` | ≥1 search/retrieval/ingestion facts | INFORMATIONAL | `ai_readiness.search_and_retrieval_readiness` |
| AI-022 | `ai_readiness.ai-022` | ≥1 vector/embeddings (data) or embeddings_usage (AI) | INFORMATIONAL | `ai_readiness.rag_enabling_assets` |
| AI-030 | `ai_readiness.ai-030` | ≥1 LLM SDK or AI framework | INFORMATIONAL | `ai_readiness.existing_ai_llm_integrations` |
| AI-031 | `ai_readiness.ai-031` | ≥1 prompt assets | INFORMATIONAL | `ai_readiness.existing_ai_llm_integrations` |
| AI-032 | `ai_readiness.ai-032` | ≥1 RAG pipeline | INFORMATIONAL | `ai_readiness.rag_enabling_assets` |
| AI-040 | `ai_readiness.ai-040` | ≥1 known tool/MCP facts | INFORMATIONAL | `ai_readiness.tool_and_mcp_integration` |
| AI-041 | `ai_readiness.ai-041` | ≥1 known workflow/agent facts | INFORMATIONAL | `ai_readiness.workflow_and_agent_boundaries` |
| AI-050 | `ai_readiness.ai-050` | ≥1 known observability/governance facts | INFORMATIONAL | `ai_readiness.observability_and_governance` |
| AI-051 | `ai_readiness.ai-051` | AI-related assets present; zero known obs facts (suppressed when AI-050 matches) | LOW | `ai_readiness.observability_and_governance` |
| AI-060 | `ai_readiness.ai-060` | ≥3 distinct evidence families | INFORMATIONAL | `ai_readiness.miscellaneous` |
| AI-061 | `ai_readiness.ai-061` | AI-related assets; &lt;3 active families (suppressed when AI-060 matches) | LOW | `ai_readiness.miscellaneous` |

Severity is limited to **Informational** and **Low**. No Medium/High/Critical.

## Precision notes

- Confidence is derived only from observed confirmation levels
  (structurally confirmed → HIGH; inspected/declared/configured → MEDIUM;
  otherwise LOW).
- AI-060 does **not** claim the repository is AI ready or agent ready.
- AI-003 / AI-011 / AI-051 / AI-061 are observation-only gap signals — they do
  not prescribe modernization work.
- Empty / unusable evidence → rules are not applicable (no Findings).

## Finding identity

Finding IDs use `finding:{rule_id}:{digest}` from stable subject keys.
Shuffle of input fact order must not change Finding IDs or serialized bytes.

## Privacy

Findings may include relative paths and technology identifiers. Absolute
filesystem paths and source bodies are never serialized. Remediation text is
an observation-only note (no modernization advice).

## Explicit exclusions (this phase)

- No themes / conclusions / recommendations (inventory is Phase 4.8.4)
- No synthesis or scoring
- No report adapter / CTO narrative
- No AI/LLM execution
- No new evidence collectors

Zero findings does **not** mean the repository is AI ready or free of
AI-readiness gaps.

## Related

- Evidence: [../repository-ai-readiness-evidence.md](../repository-ai-readiness-evidence.md)
- Configuration: [configuration.md](configuration.md)
- Pack package: `aimf.application.rules.ai_readiness`

# Repository AI-Readiness Evidence (Phase 4.8.2)

Platform evidence for repository-observable AI/agent readiness signals.
**Not** owned by AI Readiness Intelligence assessment.

## Ownership

| Concern | Owner |
| ------- | ----- |
| Discovery / API / docs / data / AI / tool / workflow / observability facts | Platform `repository_ai_readiness` evidence |
| AI Readiness Intelligence interpretation | Deferred (future AI Readiness rules) |
| Findings / severity / readiness scores | Not in this phase |

Collectors must not import `aimf.domain.ai_readiness` /
`aimf.application.ai_readiness` and must not emit Findings.

## Contract

| Constant | Value |
| -------- | ----- |
| Schema | `repository-ai-readiness-evidence` **1.0.0** |
| Artifact | `repository-ai-readiness-evidence.json` |
| Schema ID | `codestrata.repository_ai_readiness_evidence` |
| Provider | `repository_ai_readiness.discovery` @ `1.0.0` |
| Aggregate | `AggregatedRepositoryAiReadinessEvidence` |

## Detected families

1. **API boundary** — OpenAPI/Swagger, gRPC/proto, controllers/routers/handlers, GraphQL
2. **Documentation** — README, ADRs, architecture docs, API docs, schema dictionaries
3. **Data retrieval** — repositories/DBs, search engines, vector DBs, embeddings, ingestion/indexing
4. **AI integration** — LLM SDKs, prompts, RAG pipelines, AI frameworks, model config
5. **Tool / MCP** — MCP configs, tool definitions/schemas, plugin registries
6. **Workflow / agent** — Temporal/Airflow/Celery/Prefect, LangGraph, event consumers
7. **Observability / governance** — OTel/metrics, audit, eval assets, guardrails

## Configuration

```toml
[evidence.repository_ai_readiness]
enabled = false
# max_files = 500
# max_file_chars = 500000
# max_file_bytes = 2000000
```

Independent of `[analysis.ai_readiness]` and `[report.sections.ai_readiness]`.

## Explicit non-claims

Zero candidates does not mean AI readiness signals are absent. Presence of
candidates does not mean the repository is AI ready, agent ready, RAG-ready,
or governed for LLM usage.

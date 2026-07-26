# CodeStrata MCP Overview (Phase 5.7)

**Status:** Complete — repository-intelligence MCP tools over existing services.

CodeStrata exposes assessment, retrieval, and grounded-answer capabilities through
a standards-compliant Model Context Protocol server. MCP is an **interface layer
only**; tools delegate to existing application services.

```text
MCP Client
   ↓
CodeStrata MCP Transport (stdio | streamable-http)
   ↓
MCP Tool Registry
   ↓
MCP Application Adapters
   ↓
KnowledgeQueryService / RepositoryRetriever / GroundedAnswerEngine
```

## Principles

- Model-independent (no Bedrock/OpenAI/Anthropic/local LLM in this phase)
- Tenant + repository (+ optional scan) isolation
- Structured, bounded, traceable JSON outputs
- Never expose credentials, database URLs, env values, or embeddings
- Read-only tools (no repository mutation, shell, or arbitrary filesystem access)

## External tool names

SDK registration uses underscores. Dotted aliases map 1:1:

| External name | Registered tool |
| ------------- | --------------- |
| `repository.search` | `repository_search` |
| `repository.answer` | `repository_answer` |
| `repository.findings` | `repository_findings` |
| `repository.recommendations` | `repository_recommendations` |
| `repository.assessments` | `repository_assessments` |
| `repository.files` | `repository_files` |
| `repository.architecture` | `repository_architecture` |
| `repository.security` | `repository_security` |
| `repository.dependencies` | `repository_dependencies` |
| `repository.tests` | `repository_tests` |
| `repository.cloud` | `repository_cloud` |
| `repository.ai_readiness` | `repository_ai_readiness` |
| `repository.performance` | `repository_performance` |
| `repository.health` | `repository_health` |

Phase 2 knowledge-store tools (`list_findings`, `run_assessment`, …) remain available.

## Schemas

- `mcp-tool-response` 1.0.0
- `mcp-health-response` 1.0.0
- `mcp-server-manifest` 1.0.0

## `repository.answer` labeling

Uses `DeterministicExtractiveAnswerProvider`:

- non-generative
- non-production
- deterministic extraction only

Not an LLM-generated answer. Future production providers must keep citation and
grounding contracts.

See [setup.md](setup.md), [tools.md](tools.md), [client-examples.md](client-examples.md),
[security.md](security.md), and [troubleshooting.md](troubleshooting.md).

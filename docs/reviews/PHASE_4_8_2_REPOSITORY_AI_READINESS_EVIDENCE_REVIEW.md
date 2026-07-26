# Phase 4.8.2 — Repository AI-Readiness Evidence Review

**Date:** 2026-07-25  
**Artifacts:** `reports/dogfood-phase-4-8-2/` (gitignored)  
**Schema:** `repository-ai-readiness-evidence` **1.0.0**  
**Artifact:** `repository-ai-readiness-evidence.json`  
(`codestrata.repository_ai_readiness_evidence`)

## Recommendation

**Accept Phase 4.8.2.** Platform evidence collects deterministic
repository-observable AI/agent readiness signals only.
No AI Readiness rules, Findings, assessment inventory, synthesis, report
integration, AI execution, or readiness scores were added.

## Evidence ownership

| Concern | Owner |
| ------- | ----- |
| Path discovery + content confirmation | Platform `repository_ai_readiness` evidence |
| AI Readiness Intelligence interpretation | Deferred (future AI Readiness rules) |
| Findings / severity / remediation | Not in this phase |

Collectors do not import `aimf.domain.ai_readiness` /
`aimf.application.ai_readiness` and do not emit Findings.

## CodeStrata dogfood

| Field | Value |
| ----- | ----- |
| Status | `succeeded` |
| Schema / version | `repository-ai-readiness-evidence` / `1.0.0` |
| Bundle ID | `ai-readiness-evidence:d6e55c35d1d9723f` |
| Candidates | 287 |
| Technologies | `adr`, `architecture`, `contributing`, `docs`, `llm_sdk`, `prompt`, `readme`, `schema_dictionary`, `tool_definition`, `tool_schema`, `unknown` |
| Families | `ai_integration`, `documentation`, `tool_mcp` |
| Repeat-run bytes | **byte-identical** |

Manual notes:

- Docs-heavy tree produces many documentation candidates (expected).
- No absolute paths, Findings, or readiness scores in the artifact.
- Evidence gate is independent of `[analysis.ai_readiness]`.

## Spring Petclinic dogfood

| Field | Value |
| ----- | ----- |
| Status | `succeeded` |
| Schema / version | `repository-ai-readiness-evidence` / `1.0.0` |
| Bundle ID | `ai-readiness-evidence:8e69a998b35e038d` |
| Candidates | 10 |
| Technologies | `adr`, `controller`, `database_repository`, `readme`, `rest` |
| Families | `api_boundary`, `data_retrieval`, `documentation` |
| Repeat-run bytes | **byte-identical** |

## Synthetic AI/RAG fixture dogfood

| Field | Value |
| ----- | ----- |
| Status | `succeeded` |
| Bundle ID | `ai-readiness-evidence:0f0be8ee11abc046` |
| Candidates | 8 |
| Technologies | `ai_framework`, `langchain`, `logging_tracing_metrics`, `mcp`, `mcp_server`, `openapi`, `opentelemetry`, `prompt`, `readme`, `temporal`, `vector_db`, `workflow_engine` |
| Families | all seven evidence families represented |
| Repeat-run bytes | **byte-identical** |

## Validation

- Focused unit tests: package boundary, defaults, discovery false positives,
  confirmation levels, dedupe, deterministic serialization
- Ruff + mypy on changed packages: pass
- Rules / assessment consumption / inventory / synthesis / reporting / AI /
  git commit: **not added**

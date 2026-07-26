# Phase 4.8.3 — AI Readiness Hygiene Rules Review

**Date:** 2026-07-25  
**Artifacts:** `reports/dogfood-phase-4-8-3/` (gitignored)  
**Pack:** `ai_readiness.core` **1.0.0** (17 hygiene rules)

## Recommendation

**Accept Phase 4.8.3.** Rules consume only
`AggregatedRepositoryAiReadinessEvidence`, emit shared Findings with stable IDs,
Informational/Low severity, and observation-only remediation notes.
No assessment inventory, synthesis, scoring, reporting, AI/LLM execution, new
collectors, or git commit.

## Pipeline

```text
Repository AI-Readiness Evidence
        ↓
ai_readiness.core SharedRules
        ↓
Shared Findings
        ↓
(Phase 4.8.4 Assessment)
```

## CodeStrata dogfood

| Field | Value |
| ----- | ----- |
| Evidence candidates | 287 |
| Families | `ai_integration`, `documentation`, `tool_mcp` |
| Findings | **7** |
| Rules | AI-003, AI-010, AI-030, AI-031, AI-040, AI-051, AI-060 |
| Repeat-run bytes | **byte-identical** |

AI-003 fires (no API boundary/OpenAPI among inspected candidates). AI-051 fires
(AI-related assets without observability facts). AI-060 fires (≥3 families).

## Spring Petclinic dogfood

| Field | Value |
| ----- | ----- |
| Evidence candidates | 10 |
| Technologies | `adr`, `controller`, `database_repository`, `readme`, `rest` |
| Findings | **4** |
| Rules | AI-001, AI-010, AI-020, AI-060 |
| Repeat-run bytes | **byte-identical** |

API, architecture docs, and data-access signals observed. No AI-related assets →
AI-051/061 correctly not matched.

## Synthetic AI/RAG fixture dogfood

| Field | Value |
| ----- | ----- |
| Evidence candidates | 8 |
| Families | all seven represented |
| Findings | **8** |
| Rules | AI-002, AI-022, AI-030, AI-031, AI-040, AI-041, AI-050, AI-060 |
| Repeat-run bytes | **byte-identical** |

OpenAPI (AI-002) rather than REST controller (AI-001). Observability present →
AI-051 suppressed. Broad foundations (AI-060) suppress AI-061.

## Validation

- Unit tests: every rule + pack registration + suppression pairs + determinism +
  gate defaults
- Ruff + mypy on changed packages: pass
- Assessment inventory / synthesis / reporting / AI / git commit: **not added**

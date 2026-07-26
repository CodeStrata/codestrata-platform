# Phase 4.9.3 — Performance Hygiene Rules Review

**Date:** 2026-07-25  
**Artifacts:** `reports/dogfood-phase-4-9-3/` (gitignored)  
**Pack:** `performance.core` **1.0.0** (20 hygiene rules)

## Recommendation

**Accept Phase 4.9.3.** Rules consume only
`AggregatedRepositoryPerformanceEvidence`, emit shared Findings with stable IDs,
Informational/Low severity, and observation-only remediation notes.
No assessment inventory, synthesis, scoring, reporting, AI/LLM execution, new
collectors, or git commit.

## Pipeline

```text
Repository Performance Evidence
        ↓
performance.core SharedRules
        ↓
Shared Findings
        ↓
(Phase 4.9.4 Assessment)
```

## CodeStrata dogfood

| Field | Value |
| ----- | ----- |
| Evidence status | partially_succeeded |
| Candidates | 14 |
| Known families (rules) | `concurrency_async` (unknown caching excluded) |
| Findings | **5** |
| Rules | PERF-030, PERF-031, PERF-032, PERF-061, PERF-072 |
| Repeat-run bytes | **byte-identical** |

Executor concurrency observed without executor configuration → PERF-032.
Unknown-only caching facts do not activate the caching family. PERF-071
correctly not matched (&lt;3 known families).

## Spring Petclinic dogfood

| Field | Value |
| ----- | ----- |
| Evidence status | succeeded |
| Candidates | 12 |
| Known families | `caching`, `configuration_controls`, `data_access` |
| Findings | **7** |
| Rules | PERF-001, PERF-002, PERF-020, PERF-041, PERF-061, PERF-070, PERF-071 |
| Repeat-run bytes | **byte-identical** |

Multiple data-access kinds and caffeine caching. Datasource config suppresses
PERF-003. Caching suppresses PERF-021. No resource management → PERF-041.
Broad foundations (PERF-071) suppress PERF-072.

## Synthetic performance fixture dogfood

| Field | Value |
| ----- | ----- |
| Evidence status | succeeded |
| Candidates | 8 |
| Families | eight families represented |
| Findings | **11** |
| Rules | PERF-001, PERF-003, PERF-010, PERF-020, PERF-030, PERF-031, PERF-040, PERF-050, PERF-060, PERF-070, PERF-071 |
| Repeat-run bytes | **byte-identical** |

Thread-pool config (not datasource/timeout) → PERF-003 matches. Observability
present → PERF-061 suppressed. Resource management → PERF-041 suppressed.
Broad foundations → PERF-072 suppressed.

## Validation

- Unit tests: every rule + pack registration + suppression pairs + determinism +
  gate defaults — **pass**
- Ruff + mypy on changed packages: **pass**
- Assessment inventory / synthesis / reporting / AI / git commit: **not added**

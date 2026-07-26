# Phase 4.9.2 — Repository Performance Evidence Review

**Date:** 2026-07-25  
**Artifacts:** `reports/dogfood-phase-4-9-2/` (gitignored)  
**Schema:** `repository-performance-evidence` **1.0.0**  
**Artifact:** `repository-performance-evidence.json`  
(`codestrata.repository_performance_evidence`)

## Recommendation

**Accept Phase 4.9.2.** Platform evidence collects deterministic
repository-observable performance signals only.
No Performance rules, Findings, assessment inventory, synthesis, report
integration, AI execution, or performance scores were added.

## Evidence ownership

| Concern | Owner |
| ------- | ----- |
| Path discovery + content confirmation | Platform `repository_performance` evidence |
| Performance Intelligence interpretation | Deferred (future Performance rules) |
| Findings / severity / remediation | Not in this phase |

Collectors do not import `codestrata.domain.performance` /
`codestrata.application.performance` and do not emit Findings.

## Evidence model

`AggregatedRepositoryPerformanceEvidence` with eight fact families:

`data_access`, `blocking_operations`, `caching`, `concurrency_async`,
`resource_management`, `frontend_performance`, `observability_profiling`,
`configuration_controls`.

## CodeStrata dogfood

| Field | Value |
| ----- | ----- |
| Status | `partially_succeeded` |
| Schema / version | `repository-performance-evidence` / `1.0.0` |
| Bundle ID | `performance-evidence:243cfec377970a00` |
| Candidates | 14 |
| Technologies | `cache`, `dependency_manifest`, `executor`, `executor_service`, `unknown` |
| Families | `caching`, `concurrency_async`, `unknown` |
| Repeat-run bytes | **byte-identical** |

Manual notes:

- Sparse performance markers in this repo (expected).
- Partial success from bounded load diagnostics on some candidates.
- No absolute paths, Findings, or performance scores in the artifact.
- Evidence gate is independent of `[analysis.performance]`.

## Spring Petclinic dogfood

| Field | Value |
| ----- | ----- |
| Status | `succeeded` |
| Schema / version | `repository-performance-evidence` / `1.0.0` |
| Bundle ID | `performance-evidence:d52785902fe58d0f` |
| Candidates | 12 |
| Technologies | `cache`, `caffeine`, `datasource_config`, `dependency_manifest`, `hibernate`, `jpa`, `spring_data`, `unknown` |
| Families | `caching`, `configuration_controls`, `data_access`, `unknown` |
| Repeat-run bytes | **byte-identical** |

## Synthetic performance fixture dogfood

| Field | Value |
| ----- | ----- |
| Status | `succeeded` |
| Bundle ID | `performance-evidence:ee5c85fa42e7d19d` |
| Candidates | 8 |
| Technologies | `async`, `cache`, `completable_future`, `datasource_config`, `hikaricp`, `jpa`, `micrometer`, `spring_cache`, `sync_http_client`, `thread_pool`, `thread_sleep`, `webpack` |
| Families | all eight evidence families represented |
| Repeat-run bytes | **byte-identical** |

## Validation

- Focused unit tests: package boundary, defaults, one test per family,
  dedupe, deterministic serialization
- Ruff + mypy on changed packages: pass
- Rules / assessment consumption / inventory / synthesis / reporting / AI /
  git commit: **not added**

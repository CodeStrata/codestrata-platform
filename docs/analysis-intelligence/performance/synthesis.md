# Performance Assessment Synthesis

Phase 4.9.5 — deterministic synthesis from Performance assessment inventory.

## Contract

| Item | Value |
| ---- | ----- |
| Assessment schema | `performance-assessment` **1.2.0** |
| Synthesis version | **1.0.0** |
| Input | Inventories + Findings + rule execution facts |
| Output | Themes, conclusions, recommendations, overall posture summary |
| Gate | `analysis.performance.include_synthesis` (default `true` when analysis enabled) |

## Themes (emit only when supported)

| Theme | Trigger |
| ----- | ------- |
| Performance hygiene landscape | Always when synthesis runs |
| Rule execution coverage | Always when synthesis runs |
| Data access foundations | PERF-001 / PERF-002 / PERF-003 findings |
| Blocking operations | PERF-010 / PERF-011 findings |
| Caching foundations | PERF-020 / PERF-021 findings |
| Concurrency and asynchronous processing | PERF-030 / PERF-031 / PERF-032 findings |
| Resource management | PERF-040 / PERF-041 findings |
| Frontend performance controls | PERF-050 / PERF-051 / PERF-052 findings |
| Performance observability and profiling | PERF-060 / PERF-061 findings |
| Configuration controls | PERF-070 findings |
| Broad performance foundations | PERF-071 findings **or** ≥3 performance families observed |
| Limited supporting controls | PERF-072 findings |
| No performance findings | Zero findings + rules executed |
| Unsupported performance analysis scope | Documented limitations present |

## Non-claims

Synthesis must not claim the repository is performant, scalable, free of
latency risk, or production-ready under load. It must not invent bottlenecks,
hotspots, performance scores/grades, or modernization paths.

Severity implications stay informational / low.

Recommendations are observation-oriented (`Review …` / `Acknowledge …` /
`Validate observed …`) and link Finding IDs and Rule IDs.

## Explicit non-scope

- Report integration is deferred (presentation only)
- No AI / LLM execution
- No new evidence collectors or rules
- No performance scoring

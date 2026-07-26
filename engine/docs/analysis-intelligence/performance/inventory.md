# Performance Assessment Inventory

Phase **4.9.4** — deterministic inventory projection for Performance Intelligence.
Schema updated to **`performance-assessment` 1.2.0** with Phase **4.9.5** synthesis.

## Contract

| Item | Value |
| ---- | ----- |
| Schema | `performance-assessment` **1.2.0** |
| Input | Existing Performance Hygiene Findings + rule execution facts |
| Output | Inventories on `PerformanceAssessmentSection` |
| Consumed by | Synthesis (4.9.5) and future report (4.9.6) |

## Inventories

| Inventory | Contents |
| --------- | -------- |
| `finding_inventory` | Sorted finding IDs + counts by rule / severity / confidence |
| `rule_inventory` | Registered hygiene rules with execution status and finding counts |
| `severity_inventory` | Deterministic severity buckets |
| `confidence_inventory` | Deterministic confidence buckets |
| `performance_family_inventory` | Eight families: data_access, blocking_operations, caching, concurrency_async, resource_management, frontend_performance, observability_profiling, configuration_controls |

Finding **IDs only** — Findings are not duplicated into the assessment artifact.

Performance family coverage is derived from Finding rule IDs and metadata
(for example `data_access_kinds`, `families` on PERF-071/PERF-072). Inventory
never re-collects repository performance evidence.

## Explicit non-scope (inventory + synthesis)

- No new evidence collectors
- No new rules
- No performance scores / hotspots / latency grades
- No report / CLI / MCP / AI integration (report deferred to **4.9.6**)

Synthesis generation is documented in [synthesis.md](synthesis.md).

## Gates

Reuse existing Performance gates (default off). No new inventory config flag.

```toml
[evidence.repository_performance]
enabled = true

[rules]
enabled = true

[rules.performance]
enabled = true

[analysis.performance]
enabled = true
# include_synthesis = true
```

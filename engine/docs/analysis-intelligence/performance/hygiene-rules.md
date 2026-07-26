# Performance Hygiene Rules

Phase **4.9.3** — `performance.core` @ **1.0.0**

Rules consume **only** in-memory `AggregatedRepositoryPerformanceEvidence`.
They do not re-read repository files, invent performance scores, claim
bottlenecks, or emit modernization recommendations.

Human aliases **PERF-001** … **PERF-072** map to machine IDs
`performance.perf-00N`.

## Configuration

```toml
[evidence.repository_performance]
enabled = true

[rules]
enabled = true

[rules.performance]
enabled = true
```

All gates default to **disabled**. Rules never trigger evidence collection.
Evidence may run without rules. Enabling `[rules.performance]` does **not**
enable `[analysis.performance]`. When analysis is on, assessment uses
`assemble(...)` inventories Findings (Phase **4.9.4**) and deterministic
synthesis (Phase **4.9.5**).

Per-rule toggles (default enabled when the pack is on):

```toml
[rules.performance.perf_001]
enabled = true
# … perf_002, perf_003, perf_010, perf_011, perf_020, perf_021,
#   perf_030, perf_031, perf_032, perf_040, perf_041, perf_050,
#   perf_051, perf_052, perf_060, perf_061, perf_070, perf_071,
#   perf_072
```

## Rule catalog

| Alias | Rule ID | Trigger | Severity | Category |
| ----- | ------- | ------- | -------- | -------- |
| PERF-001 | `performance.perf-001` | ≥1 known data access kinds | INFORMATIONAL | `performance.inefficient_data_access` |
| PERF-002 | `performance.perf-002` | ≥2 distinct known data access kinds | INFORMATIONAL | `performance.inefficient_data_access` |
| PERF-003 | `performance.perf-003` | Data access present; zero datasource/timeout config (suppressed when those present) | LOW | `performance.batching_pagination` |
| PERF-010 | `performance.perf-010` | ≥1 thread sleep | INFORMATIONAL | `performance.blocking_operations` |
| PERF-011 | `performance.perf-011` | ≥1 sync HTTP / blocking DB / blocking file I/O | INFORMATIONAL | `performance.blocking_operations` |
| PERF-020 | `performance.perf-020` | ≥1 known caching | INFORMATIONAL | `performance.caching` |
| PERF-021 | `performance.perf-021` | Data access present; zero caching (suppressed when PERF-020 matches) | LOW | `performance.caching` |
| PERF-030 | `performance.perf-030` | ≥1 known concurrency | INFORMATIONAL | `performance.concurrency` |
| PERF-031 | `performance.perf-031` | Executor concurrency or thread-pool/executor config | INFORMATIONAL | `performance.concurrency` |
| PERF-032 | `performance.perf-032` | Concurrency present; zero executor config (suppressed when config present) | LOW | `performance.concurrency` |
| PERF-040 | `performance.perf-040` | ≥1 known resource management | INFORMATIONAL | `performance.resource_management` |
| PERF-041 | `performance.perf-041` | Data access or blocking present; zero resource (suppressed when PERF-040) | LOW | `performance.resource_management` |
| PERF-050 | `performance.perf-050` | ≥1 frontend bundle kinds (webpack/vite/bundle_config) | INFORMATIONAL | `performance.frontend_rendering_bundle` |
| PERF-051 | `performance.perf-051` | ≥1 frontend lazy/code-splitting kinds | INFORMATIONAL | `performance.frontend_rendering_bundle` |
| PERF-052 | `performance.perf-052` | Known frontend; zero bundle and zero lazy (suppressed when 050/051) | LOW | `performance.frontend_rendering_bundle` |
| PERF-060 | `performance.perf-060` | ≥1 known observability/profiling | INFORMATIONAL | `performance.observability_profiling` |
| PERF-061 | `performance.perf-061` | Non-obs performance assets; zero observability (suppressed when PERF-060) | LOW | `performance.observability_profiling` |
| PERF-070 | `performance.perf-070` | ≥1 known configuration controls | INFORMATIONAL | `performance.configuration_controls` |
| PERF-071 | `performance.perf-071` | ≥3 distinct evidence families | INFORMATIONAL | `performance.miscellaneous` |
| PERF-072 | `performance.perf-072` | Performance assets; &lt;3 active families (suppressed when PERF-071) | LOW | `performance.miscellaneous` |

Severity is limited to **Informational** and **Low**. No Medium/High/Critical.

## Precision notes

- Confidence is derived only from observed confirmation levels
  (structurally confirmed → HIGH; inspected/declared/configured → MEDIUM;
  otherwise LOW).
- PERF-071 does **not** claim the repository is performant or free of latency risk.
- Gap rules (PERF-003 / 021 / 032 / 041 / 052 / 061 / 072) are observation-only —
  they do not prescribe modernization work.
- Empty / unusable evidence → rules are not applicable (no Findings).

## Finding identity

Finding IDs use `finding:{rule_id}:{digest}` from stable subject keys.
Shuffle of input fact order must not change Finding IDs or serialized bytes.

## Privacy

Findings may include relative paths and technology identifiers. Absolute
filesystem paths and source bodies are never serialized. Remediation text is
an observation-only note (no modernization advice).

## Explicit exclusions (this phase)

- No performance scores / hotspots / latency grades
- No report adapter / CTO narrative (deferred to Phase 4.9.6)
- No AI/LLM execution
- No new evidence collectors

Zero findings does **not** mean the repository is performant or free of
performance gaps.

## Related

- Evidence: [../repository-performance-evidence.md](../repository-performance-evidence.md)
- Configuration: [configuration.md](configuration.md)
- Pack package: `codestrata.application.rules.performance`

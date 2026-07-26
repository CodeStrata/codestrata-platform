# Runtime performance and scalability (Phase 5.19)

CodeStrata keeps assessment semantics deterministic while bounding I/O,
memory, and concurrency for large repositories.

This page covers **platform runtime performance** (onboarding / analysis /
report generation). It is separate from the **Performance Intelligence**
domain packs under `application/performance/`.

## Goals

* Avoid repeated source-file reads across architecture and technical-debt packs
* Bound concurrent disk reads without changing finding/scoring output
* Emit phase-level timing and skip/truncate telemetry
* Keep secure default limits for source-file volume and per-file size

## Settings (`analysis.runtime`)

| Setting | Default | Purpose |
| ------- | ------- | ------- |
| `shared_source_text_cache` | `true` | Load eligible source texts once and reuse |
| `max_read_workers` | `4` | Bounded thread pool for independent file reads |
| `max_source_files` | `2000` | Cap on shared source-text map size |
| `max_source_chars` | `100000` | Per-file truncation for shared loads |
| `capture_peak_rss` | `true` | Record process RSS heuristic in timing |

Example `codestrata.toml`:

```toml
[analysis.runtime]
shared_source_text_cache = true
max_read_workers = 4
max_source_files = 2000
max_source_chars = 100000
capture_peak_rss = true
```

## Telemetry

`assessment.timing` in `report.json` includes additive Phase 5.19 fields:

* `graph_ms`, `rules_ms`, `evidence_ms`, `knowledge_ms`
* `files_loaded`, `files_skipped`
* `cache_hits`, `cache_misses`
* `peak_rss_mb`

Report generation records measured `report_ms` / `total_ms` after a **single**
HTML render (JSON is built once and patched; HTML is not rendered twice).

## Benchmarks

Deterministic harness:

```bash
.venv/bin/python scripts/bench_runtime_performance.py --baseline
.venv/bin/python scripts/bench_runtime_performance.py
.venv/bin/python scripts/bench_runtime_performance.py --compare
```

Artifacts land under `reports/performance-benchmark/`:

* `benchmark-baseline.json`
* `benchmark-optimized.json`
* `benchmark-comparison.json`
* `BENCHMARK_REPORT.md`

Targets include sample JS/PHP/C# apps, CodeStrata itself, and dogfood
workspaces (Java / PHP / C#) when present under `.codestrata/workspace/`.

## Recommended production limits

* Keep defaults above unless repositories routinely exceed 2k source files
  **and** host memory headroom is confirmed.
* Prefer `max_read_workers` of 2–4 on shared CI; up to 8 on dedicated runners.
* Do not disable `shared_source_text_cache` in production; baseline mode exists
  only for A/B measurement.

## Related

* [runtime.md](runtime.md) — assess pipeline stages
* [report-generation.md](report-generation.md) — HTML/JSON writers
* [incremental-assessment.md](incremental-assessment.md) — incremental reuse

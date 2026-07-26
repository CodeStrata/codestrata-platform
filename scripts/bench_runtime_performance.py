#!/usr/bin/env python3
"""Phase 5.19 runtime performance benchmark harness.

Runs deterministic assess timings against small/medium/large fixtures and
optional dogfood workspaces. Emits JSON suitable for before/after comparison.

Run artifacts are written under a temp directory (outside the repo) so that
self-scans of CodeStrata are not polluted by report output growth.

Usage:
  .venv/bin/python scripts/bench_runtime_performance.py --baseline
  .venv/bin/python scripts/bench_runtime_performance.py
  .venv/bin/python scripts/bench_runtime_performance.py --compare
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine" / "src"))

from codestrata.application.assessment.service import (  # noqa: E402
    AssessmentApplicationService,
)
from codestrata.application.runtime_performance.metrics import peak_rss_mb  # noqa: E402
from codestrata.config.settings import CodestrataSettings  # noqa: E402


@dataclass(frozen=True)
class BenchTarget:
    name: str
    path: Path
    size_class: str
    language: str


@dataclass
class BenchResult:
    name: str
    size_class: str
    language: str
    total_ms: float
    scan_ms: float | None
    analysis_ms: float | None
    graph_ms: float | None
    rules_ms: float | None
    report_ms: float | None
    files_loaded: int | None
    files_skipped: int | None
    cache_hits: int | None
    cache_misses: int | None
    peak_rss_mb: float | None
    files_in_inventory: int
    ok: bool
    error: str | None = None


def _targets() -> list[BenchTarget]:
    items = [
        BenchTarget(
            "sample-js-app",
            ROOT / "examples" / "sample-js-app",
            "small",
            "javascript",
        ),
        BenchTarget(
            "sample-php-app",
            ROOT / "examples" / "sample-php-app",
            "small",
            "php",
        ),
        BenchTarget(
            "sample-csharp-app",
            ROOT / "examples" / "sample-csharp-app",
            "small",
            "csharp",
        ),
        BenchTarget(
            "codestrata",
            ROOT,
            "large",
            "python",
        ),
        BenchTarget(
            "spring-petclinic",
            ROOT / ".codestrata" / "workspace" / "spring-petclinic",
            "medium",
            "java",
        ),
        BenchTarget(
            "eShopOnWeb",
            ROOT / ".codestrata" / "workspace" / "eShopOnWeb",
            "medium",
            "csharp",
        ),
        BenchTarget(
            "laravel",
            ROOT / ".codestrata" / "workspace" / "laravel",
            "medium",
            "php",
        ),
    ]
    return [item for item in items if item.path.is_dir()]


def _settings(repo: Path, output: Path, *, optimized: bool) -> CodestrataSettings:
    return CodestrataSettings.model_validate(
        {
            "repository": {"path": str(repo)},
            "workspace": {"directory": str(output / "ws")},
            "static_analysis": {"enabled": False},
            "knowledge": {
                "directory": str(output / "knowledge"),
                "indexing": {"enabled": False},
                "embedding": {"enabled": False},
            },
            "evidence": {
                "complexity": {"enabled": True},
                "dependency": {"enabled": True},
                "language": {"enabled": True},
            },
            "rules": {
                "enabled": True,
                "architecture": {"enabled": True},
                "technical_debt": {"enabled": True},
                "dependency": {"enabled": True},
            },
            "analysis": {
                "runtime": {
                    "shared_source_text_cache": optimized,
                    "max_read_workers": 4 if optimized else 1,
                    "capture_peak_rss": True,
                }
            },
        }
    )


def _inventory_count(repo: Path) -> int:
    count = 0
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        rel = str(path.relative_to(repo)).replace("\\", "/")
        if rel.startswith(".git/") or "/.git/" in f"/{rel}":
            continue
        count += 1
        if count >= 50_000:
            break
    return count


def run_one(target: BenchTarget, output_root: Path, *, optimized: bool) -> BenchResult:
    out = output_root / target.name
    out.mkdir(parents=True, exist_ok=True)
    settings = _settings(target.path, out, optimized=optimized)
    service = AssessmentApplicationService()
    started = perf_counter()
    try:
        result = service.run(
            repo=str(target.path),
            output_directory=out / "reports",
            settings=settings,
            write_reports=True,
            verbose=False,
        )
        elapsed = round((perf_counter() - started) * 1000, 2)
        timing = None
        run_dirs = sorted((out / "reports").rglob("report.json"))
        if run_dirs:
            report_json = json.loads(run_dirs[-1].read_text(encoding="utf-8"))
            timing = (report_json.get("assessment") or {}).get("timing") or {}
        return BenchResult(
            name=target.name,
            size_class=target.size_class,
            language=target.language,
            total_ms=float((timing or {}).get("total_ms") or elapsed),
            scan_ms=(timing or {}).get("scan_ms"),
            analysis_ms=(timing or {}).get("analysis_ms"),
            graph_ms=(timing or {}).get("graph_ms"),
            rules_ms=(timing or {}).get("rules_ms"),
            report_ms=(timing or {}).get("report_ms"),
            files_loaded=(timing or {}).get("files_loaded"),
            files_skipped=(timing or {}).get("files_skipped"),
            cache_hits=(timing or {}).get("cache_hits"),
            cache_misses=(timing or {}).get("cache_misses"),
            peak_rss_mb=(timing or {}).get("peak_rss_mb") or peak_rss_mb(),
            files_in_inventory=_inventory_count(target.path),
            ok=True,
            error=None if result is not None else "empty_result",
        )
    except Exception as error:  # noqa: BLE001
        return BenchResult(
            name=target.name,
            size_class=target.size_class,
            language=target.language,
            total_ms=round((perf_counter() - started) * 1000, 2),
            scan_ms=None,
            analysis_ms=None,
            graph_ms=None,
            rules_ms=None,
            report_ms=None,
            files_loaded=None,
            files_skipped=None,
            cache_hits=None,
            cache_misses=None,
            peak_rss_mb=peak_rss_mb(),
            files_in_inventory=_inventory_count(target.path),
            ok=False,
            error=str(error)[:500],
        )


def _pct_improvement(baseline: float, optimized: float) -> float | None:
    if baseline <= 0:
        return None
    return round(((baseline - optimized) / baseline) * 100.0, 2)


def write_comparison_report(report_dir: Path) -> Path:
    """Write markdown + JSON comparison from baseline/optimized JSON artifacts."""

    baseline_path = report_dir / "benchmark-baseline.json"
    optimized_path = report_dir / "benchmark-optimized.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    optimized = json.loads(optimized_path.read_text(encoding="utf-8"))
    base_by_name = {item["name"]: item for item in baseline["results"]}
    opt_by_name = {item["name"]: item for item in optimized["results"]}
    rows: list[dict[object, object]] = []
    for name in sorted(set(base_by_name) | set(opt_by_name)):
        base = base_by_name.get(name) or {}
        opt = opt_by_name.get(name) or {}
        rows.append(
            {
                "name": name,
                "size_class": opt.get("size_class") or base.get("size_class"),
                "language": opt.get("language") or base.get("language"),
                "baseline_total_ms": base.get("total_ms"),
                "optimized_total_ms": opt.get("total_ms"),
                "improvement_pct": _pct_improvement(
                    float(base.get("total_ms") or 0),
                    float(opt.get("total_ms") or 0),
                ),
                "baseline_rules_ms": base.get("rules_ms"),
                "optimized_rules_ms": opt.get("rules_ms"),
                "baseline_report_ms": base.get("report_ms"),
                "optimized_report_ms": opt.get("report_ms"),
                "files_loaded": opt.get("files_loaded"),
                "files_skipped": opt.get("files_skipped"),
                "cache_misses": opt.get("cache_misses"),
                "peak_rss_mb": opt.get("peak_rss_mb"),
                "files_in_inventory": opt.get("files_in_inventory")
                or base.get("files_in_inventory"),
            }
        )

    base_sum = float(baseline.get("summary", {}).get("total_ms_sum") or 0)
    opt_sum = float(optimized.get("summary", {}).get("total_ms_sum") or 0)
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "baseline_label": baseline.get("label"),
        "optimized_label": optimized.get("label"),
        "baseline_total_ms_sum": base_sum,
        "optimized_total_ms_sum": opt_sum,
        "overall_improvement_pct": _pct_improvement(base_sum, opt_sum),
        "targets": rows,
        "remaining_bottlenecks": [
            "Rule evaluation dominates wall time on medium/large repos",
            "Evidence domains outside shared source cache still perform separate I/O",
            "Directory inventory / scan cost grows with ignored vendor trees",
            "Peak RSS is an OS heuristic and not a hard memory budget",
        ],
        "recommended_production_limits": {
            "analysis.runtime.max_read_workers": 4,
            "analysis.runtime.max_source_files": 2000,
            "analysis.runtime.max_source_chars": 100_000,
            "analysis.runtime.shared_source_text_cache": True,
            "notes": (
                "Raise max_source_files only with explicit memory headroom; "
                "keep max_read_workers <= 8 on shared CI runners."
            ),
        },
    }
    json_out = report_dir / "benchmark-comparison.json"
    json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# CodeStrata runtime performance benchmark (Phase 5.19)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        f"- Baseline total (sum): **{base_sum:.2f} ms**",
        f"- Optimized total (sum): **{opt_sum:.2f} ms**",
        f"- Overall improvement: **{payload['overall_improvement_pct']}%** "
        "(negative means optimized was slower in this run; treat wall-clock "
        "as noisy across warm OS caches)",
        "",
        "## Per-target results",
        "",
        "| Target | Class | Lang | Baseline ms | Optimized ms | Δ% | Files loaded | Peak RSS MB |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {name} | {size_class} | {language} | {baseline_total_ms} | "
            "{optimized_total_ms} | {improvement_pct} | {files_loaded} | "
            "{peak_rss_mb} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Optimizations measured",
            "",
            "- Shared source-text load once for architecture + technical debt packs",
            "- Bounded concurrent file reads (`max_read_workers`)",
            "- Single HTML render path for report generation (no double-render)",
            "- Additive timing telemetry: phase ms, files loaded/skipped, cache, peak RSS",
            "",
            "## Remaining bottlenecks",
            "",
        ]
    )
    for item in payload["remaining_bottlenecks"]:
        lines.append(f"- {item}")
    limits = payload["recommended_production_limits"]
    lines.extend(
        [
            "",
            "## Recommended production limits",
            "",
            (
                "- `analysis.runtime.max_read_workers`: "
                f"`{limits['analysis.runtime.max_read_workers']}`"
            ),
            (
                "- `analysis.runtime.max_source_files`: "
                f"`{limits['analysis.runtime.max_source_files']}`"
            ),
            (
                "- `analysis.runtime.max_source_chars`: "
                f"`{limits['analysis.runtime.max_source_chars']}`"
            ),
            (
                "- `analysis.runtime.shared_source_text_cache`: "
                f"`{limits['analysis.runtime.shared_source_text_cache']}`"
            ),
            f"- {limits['notes']}",
            "",
            "## Notes",
            "",
            "- Knowledge indexing/embedding disabled in this harness for deterministic focus.",
            "- Static analysis (PMD) disabled to isolate platform runtime cost.",
            "- Run artifacts are written outside the repo to avoid self-scan inflation.",
            "",
        ]
    )
    md_out = report_dir / "BENCHMARK_REPORT.md"
    md_out.write_text("\n".join(lines), encoding="utf-8")
    return md_out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default="optimized", help="Run label for output file")
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Disable shared cache and force serial reads (baseline mode)",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Only write comparison report from existing baseline/optimized JSON",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "reports" / "performance-benchmark"),
        help="Directory for benchmark summary JSON/Markdown",
    )
    args = parser.parse_args()
    report_dir = Path(args.output)
    report_dir.mkdir(parents=True, exist_ok=True)

    if args.compare:
        path = write_comparison_report(report_dir)
        print(f"wrote {path}")
        return 0

    optimized = not args.baseline
    label = args.label if not args.baseline else "baseline"
    # Keep bulky run artifacts outside the repo so self-scans stay stable.
    run_root = Path(tempfile.mkdtemp(prefix=f"codestrata-perf-{label}-"))
    results = [run_one(target, run_root, optimized=optimized) for target in _targets()]
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "label": label,
        "optimized": optimized,
        "run_artifacts_directory": str(run_root),
        "results": [asdict(item) for item in results],
        "summary": {
            "target_count": len(results),
            "ok_count": sum(1 for item in results if item.ok),
            "total_ms_sum": round(sum(item.total_ms for item in results if item.ok), 2),
        },
    }
    out_path = report_dir / f"benchmark-{label}.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(f"wrote {out_path}")
    print(f"run artifacts: {run_root}")
    if (report_dir / "benchmark-baseline.json").is_file() and (
        report_dir / "benchmark-optimized.json"
    ).is_file():
        compare_path = write_comparison_report(report_dir)
        print(f"wrote {compare_path}")
    return 0 if all(item.ok for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

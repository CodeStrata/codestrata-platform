#!/usr/bin/env python3
"""Official performance & scale baseline harness.

Observational only. Writes (gitignored):
  .generated/performance-benchmark.json
  per-repo run directories under .generated/performance-baseline/

Usage:
  .venv/bin/python scripts/bench_performance_baseline.py
  .venv/bin/python scripts/bench_performance_baseline.py --with-ai
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine" / "src"))

from codestrata.application.assessment.service import (  # noqa: E402
    AssessmentApplicationService,
    AssessmentCommandError,
)
from codestrata.benchmark import (  # noqa: E402
    build_run_record,
    build_suite_document,
    write_performance_benchmark,
)
from codestrata.config.settings import CodestrataSettings  # noqa: E402
from codestrata.reporting.modernization_models import AssessmentMode  # noqa: E402


TARGETS = (
    ("codestrata-platform", ROOT, "large"),
    (
        "spring-petclinic",
        ROOT / ".codestrata-examples" / "spring-petclinic",
        "medium",
    ),
    ("sample-js-app", ROOT / "test-fixtures" / "sample-js-app", "small"),
    ("sample-python-app", ROOT / "test-fixtures" / "sample-python-app", "small"),
)


def _settings(repo: Path, output: Path, *, with_ai: bool = False) -> CodestrataSettings:
    payload: dict = {
        "repository": {"path": str(repo)},
        "profile": "community",
        "workspace": {"directory": str(output / "ws")},
        "static_analysis": {"enabled": False},
        "knowledge": {"enabled": False},
        "analysis": {
            "runtime": {
                "benchmark_collection": True,
                "capture_peak_rss": True,
                "max_source_files": 20000 if repo.resolve() == ROOT.resolve() else 5000,
                "shared_source_text_cache": True,
                "max_read_workers": 4,
            }
        },
    }
    return CodestrataSettings.model_validate(payload)


def _run_one(
    *,
    label: str,
    repo: Path,
    output_root: Path,
    with_ai: bool,
) -> object:
    out = output_root / label
    out.mkdir(parents=True, exist_ok=True)
    settings = _settings(repo, out, with_ai=with_ai)
    service = AssessmentApplicationService()
    mode = AssessmentMode.AI_ENHANCED if with_ai else AssessmentMode.DETERMINISTIC
    try:
        result = service.run(
            repo=str(repo),
            output_directory=out,
            mode=mode,
            settings=settings,
            quiet=True,
            write_reports=True,
        )
        run = build_run_record(
            label=label,
            repository_path=repo,
            run_directory=result.run_directory,
            report_json_path=result.json_report_path,
            command_result=result,
            ai_requested=with_ai,
        )
        # Prefer the live per-run artifact if present (includes recorder stages).
        live = result.run_directory / "performance-benchmark.json"
        if live.is_file():
            payload = json.loads(live.read_text(encoding="utf-8"))
            if payload.get("runs"):
                from codestrata.benchmark.models import PerformanceBenchmarkRun

                run = PerformanceBenchmarkRun.model_validate(payload["runs"][0])
                run = run.model_copy(update={"label": label})
        return run
    except AssessmentCommandError as error:
        return build_run_record(
            label=label,
            repository_path=repo,
            run_directory=None,
            status="failed",
            failure={
                "error_type": "AssessmentCommandError",
                "message": str(error)[:500],
            },
            ai_requested=with_ai,
        )


def _failure_limits(output_root: Path) -> list:
    from codestrata.benchmark.models import PerformanceBenchmarkRun

    cases = []
    # Missing repository
    try:
        AssessmentApplicationService().run(
            repo=str(output_root / "does-not-exist"),
            output_directory=output_root / "failure-missing",
            settings=_settings(ROOT / "test-fixtures" / "sample-js-app", output_root),
            quiet=True,
        )
        cases.append(
            PerformanceBenchmarkRun(
                run_id="failure-missing",
                label="failure-missing-repo",
                status="unexpected_success",
            )
        )
    except AssessmentCommandError as error:
        cases.append(
            build_run_record(
                label="failure-missing-repo",
                repository_path=output_root / "does-not-exist",
                run_directory=None,
                status="failed_expected",
                failure={"message": str(error)[:300]},
            )
        )

    # Empty repository
    empty = output_root / "empty-repo"
    empty.mkdir(parents=True, exist_ok=True)
    try:
        result = AssessmentApplicationService().run(
            repo=str(empty),
            output_directory=output_root / "failure-empty",
            settings=_settings(empty, output_root),
            quiet=True,
        )
        cases.append(
            build_run_record(
                label="failure-empty-repo",
                repository_path=empty,
                run_directory=result.run_directory,
                report_json_path=result.json_report_path,
                command_result=result,
                status="completed",
                notes=["empty repository completed without crash"],
            )
        )
    except AssessmentCommandError as error:
        cases.append(
            build_run_record(
                label="failure-empty-repo",
                repository_path=empty,
                run_directory=None,
                status="failed_expected",
                failure={"message": str(error)[:300]},
            )
        )
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-ai",
        action="store_true",
        help="Also attempt CodeStrata Platform with --with-ai semantics",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / ".generated",
        help="Directory for suite performance-benchmark.json",
    )
    args = parser.parse_args()

    output_root = ROOT / ".generated" / "performance-baseline"
    output_root.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)

    runs = []
    for label, path, _size in TARGETS:
        if not path.is_dir():
            runs.append(
                build_run_record(
                    label=label,
                    repository_path=path,
                    run_directory=None,
                    status="skipped",
                    failure={"reason": "repository_path_missing"},
                )
            )
            continue
        print(f"benchmarking {label} ...", flush=True)
        runs.append(_run_one(label=label, repo=path, output_root=output_root, with_ai=False))

    if args.with_ai:
        print("benchmarking codestrata-platform with AI ...", flush=True)
        runs.append(
            _run_one(
                label="codestrata-platform-with-ai",
                repo=ROOT,
                output_root=output_root,
                with_ai=True,
            )
        )

    print("validating failure limits ...", flush=True)
    with tempfile.TemporaryDirectory(prefix="codestrata-bench-fail-") as tmp:
        runs.extend(_failure_limits(Path(tmp)))

    document = build_suite_document(runs)
    suite_path = write_performance_benchmark(
        document,
        args.output / "performance-benchmark.json",
    )
    print(f"wrote {suite_path}", flush=True)
    return 0 if document.summary.get("failed_count", 0) == 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())

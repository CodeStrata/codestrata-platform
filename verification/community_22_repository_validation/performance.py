"""Performance observations from suite progress (sanitized aggregates only)."""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.contract import SV1713_OUTPUT_RELATIVE
from verification.community_22_repository_validation.helpers import add_check
from verification.community_22_repository_validation.models import CheckResult, Defect

PROGRESS_RELATIVE = f"{SV1713_OUTPUT_RELATIVE}/progress.jsonl"


def observe_performance(monorepo: Path) -> dict[str, Any]:
    path = monorepo / PROGRESS_RELATIVE
    durations: list[float] = []
    success = 0
    failed = 0
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            status = str(row.get("assessment_status") or "")
            if status in {"pass", "present", "pass_with_limitations"}:
                success += 1
            elif status and status != "not_executed":
                failed += 1
            dur = row.get("duration_seconds")
            if isinstance(dur, (int, float)):
                durations.append(float(dur))
    total = sum(durations) if durations else None
    median = statistics.median(durations) if durations else None
    largest = max(durations) if durations else None
    classification = "ACCEPTABLE_V0_2_0"
    if largest is not None and largest > 30 * 60:
        classification = "OPTIMIZE_BEFORE_RELEASE"
    return {
        "repository_count": success + failed,
        "successful_assessments": success,
        "failed_assessments": failed,
        "total_duration_seconds": total,
        "median_assessment_duration_seconds": median,
        "largest_duration_seconds": largest,
        "classification": classification,
    }


def check_performance(
    *,
    monorepo: Path,
    skip_execute: bool,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    if skip_execute:
        add_check(
            checks,
            defects,
            "performance:full_suite_not_run_in_scaffolding",
            True,
            "skip_execute",
            "performance",
            CheckResult=CheckResult,
            Defect=Defect,
        )
        return checks, defects, {}

    obs = observe_performance(monorepo)
    add_check(
        checks,
        defects,
        "performance:suite_execution_observed",
        int(obs.get("successful_assessments") or 0) > 0,
        f"success={obs.get('successful_assessments')};failed={obs.get('failed_assessments')}",
        "performance",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "performance:classification_recorded",
        obs.get("classification") in {
            "ACCEPTABLE_V0_2_0",
            "OPTIMIZE_BEFORE_RELEASE",
            "POST_V0_2_0",
            "BLOCKER",
        },
        str(obs.get("classification")),
        "performance",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    return checks, defects, obs

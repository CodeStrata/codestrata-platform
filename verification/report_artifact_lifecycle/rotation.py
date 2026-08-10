"""Rotation policy checks for Slice 17.15."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.report_artifact_lifecycle.contract import (
    ENGINE_LIFECYCLE,
    ENGINE_REPORT_PATHS,
    MAX_VERSIONS,
    SLOTS,
)
from verification.report_artifact_lifecycle.helpers import add_check, read_text
from verification.report_artifact_lifecycle.models import CheckResult, Defect


def check_rotation(monorepo: Path, policy: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"atomic": False, "max_versions": MAX_VERSIONS}

    add_check(
        checks,
        defects,
        "rotation:atomic_policy",
        policy.get("rotation_atomic") is True,
        str(policy.get("rotation_atomic")),
        "rotation",
    )
    add_check(
        checks,
        defects,
        "rotation:two_slots",
        list(policy.get("slots") or []) == list(SLOTS),
        str(policy.get("slots")),
        "rotation",
    )
    add_check(
        checks,
        defects,
        "rotation:assessment_max_two",
        policy.get("assessment_versions_per_repository") == MAX_VERSIONS,
        str(policy.get("assessment_versions_per_repository")),
        "rotation",
    )
    add_check(
        checks,
        defects,
        "rotation:eir_max_two",
        policy.get("engineering_intelligence_versions_per_portfolio") == MAX_VERSIONS,
        str(policy.get("engineering_intelligence_versions_per_portfolio")),
        "rotation",
    )
    add_check(
        checks,
        defects,
        "rotation:failed_assessment_no_promote",
        policy.get("failed_assessment_promotes") is False,
        str(policy.get("failed_assessment_promotes")),
        "rotation",
    )
    add_check(
        checks,
        defects,
        "rotation:failed_eir_no_promote",
        policy.get("failed_eir_promotes") is False,
        str(policy.get("failed_eir_promotes")),
        "rotation",
    )

    lifecycle_path = monorepo / ENGINE_LIFECYCLE
    if lifecycle_path.is_file():
        text = read_text(lifecycle_path)
        summary["atomic"] = "atomic" in text.lower() or "os.replace" in text
        add_check(
            checks,
            defects,
            "rotation:engine_atomic",
            summary["atomic"],
            "atomic rotation in lifecycle module",
            "rotation",
            soft=True,
        )

    report_paths = monorepo / ENGINE_REPORT_PATHS
    if report_paths.is_file():
        text = read_text(report_paths)
        retains_three = "DEFAULT_RETAINED_RUN_COUNT = 3" in text or "DEFAULT_ACTIVE_REPORT_RUNS_TO_KEEP = 3" in text
        retains_two = "DEFAULT_RETAINED_RUN_COUNT = 2" in text or "DEFAULT_ACTIVE_REPORT_RUNS_TO_KEEP = 2" in text
        add_check(
            checks,
            defects,
            "rotation:report_paths_retention_count",
            retains_two or not retains_three,
            "retention count aligned with policy (2)",
            "rotation",
            soft=retains_three and not retains_two,
        )

    return checks, defects, summary

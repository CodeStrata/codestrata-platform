"""Release boundary guards for Slice 16.8."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect


def check_release_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(
        checks,
        defects,
        "release_boundary:no_sv17_1",
        not (monorepo / "reports/verification/sv17-1").exists(),
        "sv16-10 absent",
        "release_boundary",
        classification="epic_17_started",
    )
    add_check(
        checks,
        defects,
        "release_boundary:no_repository_consistency_next_pkg",
        not (monorepo / "verification/repository_cutover").exists(),
        "no cutover package",
        "release_boundary",
    )
    return checks, defects

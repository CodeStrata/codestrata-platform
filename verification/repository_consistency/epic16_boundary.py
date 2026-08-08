"""Epic 16 boundary for Slice 16.8."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect


def check_epic16_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    add_check(
        checks,
        defects,
        "epic16:package_present",
        (monorepo / "verification/repository_consistency").is_dir(),
        "repository_consistency",
        "epic16_boundary",
    )
    add_check(
        checks,
        defects,
        "epic16:no_slice_16_9_package",
        not (monorepo / "verification/repository_cutover").is_dir()
        and not (monorepo / "verification/repository_split").is_dir(),
        "16.9 absent",
        "epic16_boundary",
        classification="epic_17_started",
    )
    # Prior slice packages still present
    for name in (
        "repository_inventory",
        "repository_documentation",
        "repository_code_cleanup",
        "repository_asset_design_cleanup",
        "repository_dependency_build_cleanup",
        "repository_storage_generated_cleanup",
        "repository_boundary_residency",
    ):
        add_check(
            checks,
            defects,
            f"epic16:prior_pkg:{name}",
            (monorepo / "verification" / name).is_dir(),
            name,
            "epic16_boundary",
        )
    return checks, defects

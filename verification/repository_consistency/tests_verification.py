"""Active tests/verification consistency (lightweight)."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect


def check_tests_verification(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    add_check(
        checks,
        defects,
        "tests:verification_tree",
        (monorepo / "tests/verification").is_dir(),
        "tests/verification",
        "tests_verification",
    )
    add_check(
        checks,
        defects,
        "tests:architecture_boundary_tests",
        (monorepo / "tests/architecture/test_engine_platform_boundary.py").is_file(),
        "engine_platform_boundary",
        "tests_verification",
    )
    # Current epic16 test packages exist
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
            f"tests:prior_sv16:{name}",
            (monorepo / "tests/verification" / name).is_dir(),
            name,
            "tests_verification",
        )
    return checks, defects

"""Epic 16 boundary checks — Slice 16.1 allowed; Slice 16.2+ forbidden."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_completion.contract import (
    FORBIDDEN_EPIC16_PACKAGES,
    FORBIDDEN_EPIC16_PATHS,
    POLICY_RELATIVE,
)
from verification.community_insights_completion.inventory import add_check, exists, load_json
from verification.community_insights_completion.models import CheckResult, Defect

ALLOWED_SV16_REPORTS = frozenset({"sv16-1", "sv16-2", "sv16-3", "sv16-4", "sv16-5", "sv16-6", "sv16-7", "sv16-8", "sv16-9", "sv16-10"})
ALLOWED_EPIC16_PACKAGES = frozenset(
    {
        "repository_inventory",
        "repository_documentation",
        "repository_code_cleanup",
        "repository_asset_design_cleanup",
        "repository_dependency_build_cleanup",
        "repository_storage_generated_cleanup",
        "repository_boundary_residency",
        "repository_consistency",
        "repository_package_release_validation",
        "repository_cleanup_completion",
    }
)


def check_epic_16_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    present = [rel for rel in FORBIDDEN_EPIC16_PATHS if exists(monorepo, rel)]
    add_check(
        checks,
        defects,
        "epic16:forbidden_paths_absent",
        not present,
        "absent" if not present else ",".join(present),
        "epic_16_boundary",
        classification="slice_16_2_started",
    )

    pkg_present = [rel for rel in FORBIDDEN_EPIC16_PACKAGES if exists(monorepo, rel)]
    add_check(
        checks,
        defects,
        "epic16:forbidden_packages_absent",
        not pkg_present,
        "absent" if not pkg_present else ",".join(pkg_present),
        "epic_16_boundary",
        classification="slice_16_2_started",
    )

    reports = monorepo / "reports" / "verification"
    sv16: list[str] = []
    if reports.is_dir():
        sv16 = sorted(
            p.name
            for p in reports.iterdir()
            if p.is_dir() and p.name.startswith("sv16-")
        )
    disallowed_sv16 = [n for n in sv16 if n not in ALLOWED_SV16_REPORTS]
    add_check(
        checks,
        defects,
        "epic16:only_sv16_1_reports_allowed",
        not disallowed_sv16,
        "sv16-1_only" if not disallowed_sv16 else ",".join(disallowed_sv16),
        "epic_16_boundary",
        classification="slice_16_2_started",
    )

    ver_root = monorepo / "verification"
    epic16_pkgs: list[str] = []
    if ver_root.is_dir():
        epic16_pkgs = sorted(
            p.name
            for p in ver_root.iterdir()
            if p.is_dir()
            and (
                p.name.startswith("repository_cleanup")
                or p.name.startswith("epic16_")
                or "epic_16" in p.name.lower()
            )
            and p.name not in ALLOWED_EPIC16_PACKAGES
        )
    add_check(
        checks,
        defects,
        "epic16:no_slice_16_2_packages",
        not epic16_pkgs,
        "absent" if not epic16_pkgs else ",".join(epic16_pkgs),
        "epic_16_boundary",
        classification="slice_16_2_started",
    )

    policy = load_json(monorepo, POLICY_RELATIVE)
    add_check(
        checks,
        defects,
        "epic16:start_slice_16_5_true",
        policy.get("start_slice_16_5", False) is True,
        str(policy.get("start_slice_16_5", False)),
        "epic_16_boundary",
    )
    add_check(
        checks,
        defects,
        "epic16:start_slice_16_6_true",
        policy.get("start_slice_16_6", False) is True,
        str(policy.get("start_slice_16_6", False)),
        "epic_16_boundary",
    )
    add_check(
        checks,
        defects,
        "epic16:start_slice_16_7_true",
        policy.get("start_slice_16_7", False) is True,
        str(policy.get("start_slice_16_7", False)),
        "epic_16_boundary",
    )
    add_check(
        checks,
        defects,
        "epic16:start_slice_16_8_true",
        policy.get("start_slice_16_8", False) is True,
        str(policy.get("start_slice_16_8", False)),
        "epic_16_boundary",
    )
    add_check(
        checks,
        defects,
        "epic16:start_slice_16_9_true",
        policy.get("start_slice_16_9", False) is True,
        str(policy.get("start_slice_16_9", False)),
        "epic_16_boundary",
    )
    add_check(
        checks,
        defects,
        "epic16:start_slice_16_10_true",
        policy.get("start_slice_16_10", False) is True,
        str(policy.get("start_slice_16_10", False)),
        "epic_16_boundary",
        classification="slice_16_10_started",
    )
    add_check(
        checks,
        defects,
        "epic16:start_epic_16_true",
        policy.get("start_epic_16") is True,
        str(policy.get("start_epic_16")),
        "epic_16_boundary",
    )
    return checks, defects

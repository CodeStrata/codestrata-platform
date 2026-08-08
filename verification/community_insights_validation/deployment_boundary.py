"""Deployment and slice boundary checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.contract import (
    ALLOWED_PRIOR_REPORT_DIRS,
    FORBIDDEN_15_12_PATHS,
    POLICY_RELATIVE,
    PRIOR_SLICE_PACKAGES,
)
from verification.community_insights_validation.inventory import exists, load_json
from verification.community_insights_validation.models import CheckResult, Defect


def check_deployment_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)

    add_check(
        checks,
        defects,
        "deployment:production_disabled",
        policy.get("production_deployment_enabled") is False,
        "disabled",
        "deployment_boundary",
    )
    add_check(
        checks,
        defects,
        "deployment:live_dashboard_unavailable",
        policy.get("live_dashboard_data_available") is False,
        "unavailable",
        "deployment_boundary",
    )

    present = [rel for rel in FORBIDDEN_15_12_PATHS if exists(monorepo, rel)]
    add_check(
        checks,
        defects,
        "boundary:slice_15_12_not_started",
        not present,
        "absent" if not present else ",".join(present),
        "deployment_boundary",
    )

    for slice_id, package in PRIOR_SLICE_PACKAGES:
        add_check(
            checks,
            defects,
            f"boundary:prior_{slice_id}_package",
            exists(monorepo, package),
            "present",
            "deployment_boundary",
        )

    reports = monorepo / "reports" / "verification"
    later: list[str] = []
    if reports.is_dir():
        later = sorted(
            p.name
            for p in reports.iterdir()
            if p.is_dir()
            and p.name.startswith("sv15-")
            and p.name not in ALLOWED_PRIOR_REPORT_DIRS
        )
    add_check(
        checks,
        defects,
        "boundary:no_later_slice_reports",
        not later,
        "absent" if not later else ",".join(later),
        "deployment_boundary",
    )
    return checks, defects

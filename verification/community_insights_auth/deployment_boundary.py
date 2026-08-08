"""Deployment boundary checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check
from verification.community_insights_auth.contract import FORBIDDEN_15_10_PATHS
from verification.community_insights_auth.inventory import exists, load_json
from verification.community_insights_auth.models import CheckResult, Defect


def check_deployment_boundary(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, "platform/policies/community_insights_auth_policy.json")

    add_check(
        checks,
        defects,
        "deployment:production_disabled",
        policy.get("production_deployment_enabled") is False,
        "disabled",
        "deployment_boundary",
    )
    present = [rel for rel in FORBIDDEN_15_10_PATHS if exists(monorepo, rel)]
    add_check(
        checks,
        defects,
        "deployment:slice_15_10_not_started",
        not present,
        "absent" if not present else "present",
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
            and p.name
            not in {
                "sv15-1",
                "sv15-2",
                "sv15-3",
                "sv15-4",
                "sv15-5",
                "sv15-6",
                "sv15-7",
                "sv15-8",
                "sv15-9",
                "sv15-10",
                "sv15-11",
                "sv15-12",
                "sv16-1",
            }
        )
    add_check(
        checks,
        defects,
        "deployment:no_later_slice_reports",
        not later,
        "absent" if not later else "present",
        "deployment_boundary",
    )
    return checks, defects

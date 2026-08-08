"""Aggregation boundary checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check
from verification.community_insights_auth.contract import AUTH_PACKAGE
from verification.community_insights_auth.inventory import read_text
from verification.community_insights_auth.models import CheckResult, Defect


def check_aggregation_boundary(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    insights_service = read_text(
        monorepo,
        "platform/src/codestrata_platform/community_cloud_api/insights/service.py",
    )
    auth_service = read_text(monorepo, f"{AUTH_PACKAGE}/service.py")

    add_check(
        checks,
        defects,
        "aggregation:no_password_in_aggregation",
        "verify_password" not in insights_service and "dashboard-password" not in insights_service,
        "absent",
        "aggregation_boundary",
    )
    add_check(
        checks,
        defects,
        "aggregation:auth_does_not_aggregate_for_login",
        "aggregate_metric" not in auth_service and "aggregate_dashboard" not in auth_service,
        "separate",
        "aggregation_boundary",
    )
    return checks, defects

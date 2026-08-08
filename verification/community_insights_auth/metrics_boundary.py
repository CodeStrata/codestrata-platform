"""Metrics boundary checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check
from verification.community_insights_auth.contract import AUTH_PACKAGE
from verification.community_insights_auth.inventory import read_text
from verification.community_insights_auth.models import CheckResult, Defect


def check_metrics_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    routes = read_text(monorepo, f"{AUTH_PACKAGE}/routes.py")
    handlers = read_text(monorepo, f"{AUTH_PACKAGE}/handlers.py")

    add_check(
        checks,
        defects,
        "metrics:overview_route_registered",
        "insights.api.overview" in routes,
        "present",
        "metrics_boundary",
    )
    add_check(
        checks,
        defects,
        "metrics:no_raw_event_routes",
        "raw_event" not in routes.lower() and "/events" not in routes,
        "absent",
        "metrics_boundary",
    )
    add_check(
        checks,
        defects,
        "metrics:handler_delegates_aggregation",
        "InsightsAggregationService" in handlers,
        "delegated",
        "metrics_boundary",
    )
    return checks, defects

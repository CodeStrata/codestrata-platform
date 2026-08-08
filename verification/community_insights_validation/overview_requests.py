"""Overview request static checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.inventory import read_text
from verification.community_insights_validation.models import CheckResult, Defect


def check_overview_requests(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    dashboard = read_text(monorepo, "insights/src/pages/DashboardPage.tsx")
    auth_client = read_text(monorepo, "insights/src/api/authClient.ts")
    insights_api = read_text(monorepo, "insights/src/api/insightsApi.ts")

    add_check(
        checks,
        defects,
        "overview:single_getOverview",
        "getOverview" in dashboard and dashboard.count("getMetric(") == 0,
        "single_batch",
        "ui",
    )
    add_check(
        checks,
        defects,
        "overview:no_polling",
        "setInterval" not in dashboard and "WebSocket" not in dashboard,
        "absent",
        "ui",
    )
    add_check(
        checks,
        defects,
        "overview:auth_client_endpoint",
        "/insights/api/overview" in auth_client,
        "present",
        "auth",
    )
    add_check(
        checks,
        defects,
        "overview:api_client_method",
        "getOverview" in insights_api,
        "present",
        "ui",
    )
    return checks, defects

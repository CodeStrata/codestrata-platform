"""Completion gate for Slice 15.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_completion.inventory import (
    add_check,
    exists,
    load_json,
    prior_status,
)
from verification.community_insights_completion.models import CheckResult, Defect


def check_dashboard(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "15.10")
    add_check(checks, defects, "dashboard:prior_15_10", ok, detail, "dashboard")
    add_check(checks, defects, "dashboard:policy_present", exists(monorepo, "platform/policies/codestrata_insights_dashboard_policy.json"), "present", "dashboard")
    policy = load_json(monorepo, "platform/policies/codestrata_insights_dashboard_policy.json")
    add_check(checks, defects, "dashboard:policy_id", policy.get("policy_id") == "codestrata-insights-dashboard-policy", str(policy.get("policy_id")), "dashboard")
    add_check(checks, defects, "dashboard:page", exists(monorepo, "insights/src/pages/DashboardPage.tsx"), "present", "dashboard")
    return checks, defects

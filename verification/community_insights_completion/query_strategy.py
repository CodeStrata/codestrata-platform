"""Completion gate for Slice 15.5."""

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


def check_query_strategy(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "15.5")
    add_check(checks, defects, "query_strategy:prior_15_5", ok, detail, "query_strategy")
    add_check(checks, defects, "query_strategy:policy_present", exists(monorepo, "platform/policies/community_insights_query_policy.json"), "present", "query_strategy")
    policy = load_json(monorepo, "platform/policies/community_insights_query_policy.json")
    add_check(checks, defects, "query_strategy:policy_id", policy.get("policy_id") == "community-insights-query-policy", str(policy.get("policy_id")), "query_strategy")
    add_check(checks, defects, "query_strategy:planner", exists(monorepo, "platform/src/codestrata_platform/community_cloud_api/insights_query/planner.py"), "present", "query_strategy")
    return checks, defects

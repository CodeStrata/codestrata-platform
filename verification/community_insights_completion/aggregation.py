"""Completion gate for Slice 15.7."""

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


def check_aggregation(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "15.7")
    add_check(checks, defects, "aggregation:prior_15_7", ok, detail, "aggregation")
    add_check(checks, defects, "aggregation:policy_present", exists(monorepo, "platform/policies/community_insights_aggregation_policy.json"), "present", "aggregation")
    policy = load_json(monorepo, "platform/policies/community_insights_aggregation_policy.json")
    add_check(checks, defects, "aggregation:policy_id", policy.get("policy_id") == "community-insights-aggregation-policy", str(policy.get("policy_id")), "aggregation")
    add_check(checks, defects, "aggregation:service", exists(monorepo, "platform/src/codestrata_platform/community_cloud_api/insights/service.py"), "present", "aggregation")
    return checks, defects

"""Completion gate for Slice 15.6."""

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


def check_metrics(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "15.6")
    add_check(checks, defects, "metrics:prior_15_6", ok, detail, "metrics")
    add_check(checks, defects, "metrics:policy_present", exists(monorepo, "platform/policies/community_insights_metrics_policy.json"), "present", "metrics")
    policy = load_json(monorepo, "platform/policies/community_insights_metrics_policy.json")
    add_check(checks, defects, "metrics:policy_id", policy.get("policy_id") == "community-insights-metrics-policy", str(policy.get("policy_id")), "metrics")
    add_check(checks, defects, "metrics:contract", exists(monorepo, "platform/policies/community_insights_metrics_contract.json"), "present", "metrics")
    return checks, defects

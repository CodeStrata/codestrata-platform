"""Completion gate for Slice 15.2."""

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


def check_partitioning(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "15.2")
    add_check(checks, defects, "partitioning:prior_15_2", ok, detail, "partitioning")
    add_check(checks, defects, "partitioning:policy_present", exists(monorepo, "platform/policies/community_analytics_partition_policy.json"), "present", "partitioning")
    policy = load_json(monorepo, "platform/policies/community_analytics_partition_policy.json")
    add_check(checks, defects, "partitioning:policy_id", policy.get("policy_id") == "community-analytics-partition-policy", str(policy.get("policy_id")), "partitioning")
    add_check(checks, defects, "partitioning:contract", exists(monorepo, "platform/docs/community-cloud-api/community-analytics-partition.md"), "present", "partitioning")
    return checks, defects

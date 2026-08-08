"""Completion gate for Slice 15.1."""

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


def check_data_lake(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "15.1")
    add_check(checks, defects, "data_lake:prior_15_1", ok, detail, "data_lake")
    add_check(checks, defects, "data_lake:policy_present", exists(monorepo, "platform/policies/community_data_lake_policy.json"), "present", "data_lake")
    policy = load_json(monorepo, "platform/policies/community_data_lake_policy.json")
    add_check(checks, defects, "data_lake:policy_id", policy.get("policy_id") == "community-data-lake-policy", str(policy.get("policy_id")), "data_lake")
    add_check(checks, defects, "data_lake:module", exists(monorepo, "platform/src/codestrata_platform/community_cloud_api/data_lake/policy.py"), "present", "data_lake")
    return checks, defects

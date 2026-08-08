"""Completion gate for Slice 15.9."""

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


def check_authentication(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "15.9")
    add_check(checks, defects, "authentication:prior_15_9", ok, detail, "authentication")
    add_check(checks, defects, "authentication:policy_present", exists(monorepo, "platform/policies/community_insights_auth_policy.json"), "present", "authentication")
    policy = load_json(monorepo, "platform/policies/community_insights_auth_policy.json")
    add_check(checks, defects, "authentication:policy_id", policy.get("policy_id") == "community-insights-auth-policy", str(policy.get("policy_id")), "authentication")
    add_check(checks, defects, "authentication:infra", exists(monorepo, "infrastructure/modules/community-insights-auth"), "present", "authentication")
    return checks, defects

"""Completion gate for Slice 15.11."""

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


def check_system_validation(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "15.11")
    add_check(checks, defects, "system_validation:prior_15_11", ok, detail, "system_validation")
    add_check(checks, defects, "system_validation:policy_present", exists(monorepo, "platform/policies/community_insights_validation_policy.json"), "present", "system_validation")
    policy = load_json(monorepo, "platform/policies/community_insights_validation_policy.json")
    add_check(checks, defects, "system_validation:policy_id", policy.get("policy_id") == "community-insights-validation-policy", str(policy.get("policy_id")), "system_validation")
    add_check(checks, defects, "system_validation:package", exists(monorepo, "verification/community_insights_validation/runner.py"), "present", "system_validation")
    return checks, defects

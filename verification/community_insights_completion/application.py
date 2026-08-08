"""Completion gate for Slice 15.8."""

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


def check_application(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "15.8")
    add_check(checks, defects, "application:prior_15_8", ok, detail, "application")
    add_check(checks, defects, "application:policy_present", exists(monorepo, "platform/policies/codestrata_insights_application_policy.json"), "present", "application")
    policy = load_json(monorepo, "platform/policies/codestrata_insights_application_policy.json")
    add_check(checks, defects, "application:policy_id", policy.get("policy_id") == "codestrata-insights-application-policy", str(policy.get("policy_id")), "application")
    add_check(checks, defects, "application:root", exists(monorepo, "insights/package.json"), "present", "application")
    return checks, defects

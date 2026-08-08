"""Completion gate for Slice 15.3."""

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


def check_event_coverage(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "15.3")
    add_check(checks, defects, "event_coverage:prior_15_3", ok, detail, "event_coverage")
    add_check(checks, defects, "event_coverage:policy_present", exists(monorepo, "platform/policies/community_insights_event_coverage_policy.json"), "present", "event_coverage")
    policy = load_json(monorepo, "platform/policies/community_insights_event_coverage_policy.json")
    add_check(checks, defects, "event_coverage:policy_id", policy.get("policy_id") == "community-insights-event-coverage-policy", str(policy.get("policy_id")), "event_coverage")
    return checks, defects

"""Completion gate for Slice 15.4."""

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


def check_ingestion(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "15.4")
    add_check(checks, defects, "ingestion:prior_15_4", ok, detail, "ingestion")
    add_check(checks, defects, "ingestion:policy_present", exists(monorepo, "platform/policies/community_insights_ingestion_policy.json"), "present", "ingestion")
    policy = load_json(monorepo, "platform/policies/community_insights_ingestion_policy.json")
    add_check(checks, defects, "ingestion:policy_id", policy.get("policy_id") == "community-insights-ingestion-policy", str(policy.get("policy_id")), "ingestion")
    add_check(checks, defects, "ingestion:contract_doc", exists(monorepo, "platform/docs/community-cloud-api/community-insights-ingestion.md"), "present", "ingestion")
    return checks, defects

"""Production analytics data boundary gate."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_completion.contract import POLICY_RELATIVE
from verification.community_insights_completion.inventory import add_check, load_json
from verification.community_insights_completion.models import CheckResult, Defect


def check_production_data(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    add_check(checks, defects, "production_data:ingestion_disabled", policy.get("production_ingestion_enabled") is False, str(policy.get("production_ingestion_enabled")), "production_data")
    add_check(checks, defects, "production_data:live_dashboard_unavailable", policy.get("live_dashboard_data_available") is False, str(policy.get("live_dashboard_data_available")), "production_data")
    validation = load_json(monorepo, "platform/policies/community_insights_validation_policy.json")
    add_check(checks, defects, "production_data:validation_offline", validation.get("offline_only") is True, str(validation.get("offline_only")), "production_data")
    return checks, defects

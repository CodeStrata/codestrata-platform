"""Low-cost analytics architecture gate."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_completion.contract import POLICY_RELATIVE
from verification.community_insights_completion.inventory import add_check, load_json
from verification.community_insights_completion.models import CheckResult, Defect


def check_low_cost(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    add_check(checks, defects, "low_cost:direct_s3", policy.get("direct_s3_strategy") is True, str(policy.get("direct_s3_strategy")), "low_cost")
    for flag in ("athena_required", "glue_required", "analytics_database_required", "redis_required"):
        add_check(checks, defects, f"low_cost:{flag}_false", policy.get(flag) is False, str(policy.get(flag)), "low_cost")
    return checks, defects

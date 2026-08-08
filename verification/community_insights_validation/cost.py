"""Cost unit checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check, ensure_platform_importable
from verification.community_insights_validation.contract import POLICY_RELATIVE
from verification.community_insights_validation.inventory import load_json, read_text
from verification.community_insights_validation.models import CheckResult, Defect


def check_cost(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ensure_platform_importable(monorepo)
    from codestrata_platform.community_cloud_api.insights.cache import cache_posture
    from codestrata_platform.community_cloud_api.insights.checkpoint import checkpoint_posture

    cache = cache_posture()
    checkpoint = checkpoint_posture()
    add_check(
        checks,
        defects,
        "cost:cache_none",
        cache.get("mode") == "none",
        str(cache.get("mode")),
        "query_bounds",
    )
    add_check(
        checks,
        defects,
        "cost:checkpoint_retention_only",
        checkpoint.get("mode") == "retention_only_with_limitation",
        str(checkpoint.get("mode")),
        "query_bounds",
    )

    dashboard_policy = load_json(
        monorepo, "platform/policies/codestrata_insights_dashboard_policy.json"
    )
    add_check(
        checks,
        defects,
        "cost:overview_batch_preferred",
        dashboard_policy.get("overview_batch_preferred") is True,
        str(dashboard_policy.get("overview_batch_preferred")),
        "query_bounds",
    )

    service = read_text(
        monorepo,
        "platform/src/codestrata_platform/community_cloud_api/insights/service.py",
    )
    add_check(
        checks,
        defects,
        "cost:single_overview_service",
        "aggregate_dashboard_overview" in service,
        "present",
        "query_bounds",
    )
    _ = POLICY_RELATIVE
    return checks, defects

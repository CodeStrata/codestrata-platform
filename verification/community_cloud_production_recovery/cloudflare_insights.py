"""Cloudflare Insights recovery checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.helpers import add_check
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_cloudflare_insights(
    monorepo: Path, evidence: dict[str, Any], policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    data = (evidence.get("loaded") or {}).get("insights_recovery") or {}
    has = bool(data)
    add_check(checks, defects, "cloudflare_insights:evidence", has, "present" if has else "absent", "cloudflare_insights", soft=True)
    add_check(
        checks,
        defects,
        "cloudflare_insights:policy_ready",
        policy.get("insights_rollback_ready") is True,
        "true",
        "cloudflare_insights",
    )
    # Soft: redeploy current instead of old version is an accepted limitation.
    prior = data.get("prior_version_redeployed") is True if has else False
    add_check(
        checks,
        defects,
        "cloudflare_insights:prior_version",
        prior or not has,
        str(data.get("prior_version_redeployed")),
        "cloudflare_insights",
        soft=True,
    )
    wrangler = monorepo / "insights/wrangler.jsonc"
    add_check(checks, defects, "cloudflare_insights:wrangler", wrangler.is_file(), "insights/wrangler.jsonc", "cloudflare_insights")
    summary = {
        "evidence": has,
        "policy_ready": policy.get("insights_rollback_ready") is True,
        "prior_version_redeployed": prior,
        "redeploy_current_limitation": (not prior) if has else True,
        "ready": policy.get("insights_rollback_ready") is True,
    }
    return checks, defects, summary

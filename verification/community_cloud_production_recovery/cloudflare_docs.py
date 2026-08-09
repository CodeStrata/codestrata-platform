"""Cloudflare Docs recovery checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.helpers import add_check
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_cloudflare_docs(
    monorepo: Path, evidence: dict[str, Any], policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    data = (evidence.get("loaded") or {}).get("docs_recovery") or {}
    has = bool(data)
    add_check(checks, defects, "cloudflare_docs:evidence", has, "present" if has else "absent", "cloudflare_docs", soft=True)
    add_check(
        checks,
        defects,
        "cloudflare_docs:policy_ready",
        policy.get("docs_rollback_ready") is True,
        "true",
        "cloudflare_docs",
    )
    prior = data.get("prior_version_redeployed") is True if has else False
    add_check(
        checks,
        defects,
        "cloudflare_docs:prior_version",
        prior or not has,
        str(data.get("prior_version_redeployed")),
        "cloudflare_docs",
        soft=True,
    )
    wrangler = monorepo / "docs/wrangler.jsonc"
    add_check(
        checks,
        defects,
        "cloudflare_docs:wrangler_or_site",
        wrangler.is_file() or (monorepo / "docs").is_dir(),
        "docs",
        "cloudflare_docs",
    )
    summary = {
        "evidence": has,
        "policy_ready": policy.get("docs_rollback_ready") is True,
        "prior_version_redeployed": prior,
        "redeploy_current_limitation": (not prior) if has else True,
        "ready": policy.get("docs_rollback_ready") is True,
    }
    return checks, defects, summary

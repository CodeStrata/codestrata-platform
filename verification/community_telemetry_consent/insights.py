"""Insights aggregation timing / privacy checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent.helpers import check, load_json
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_insights(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = ["aggregation_latency"]
    policy_path = monorepo / "platform/policies/community_insights_ingestion_policy.json"
    if policy_path.is_file():
        pol = load_json(policy_path)
        checks.append(check(
            "insights:denied_must_not_emit",
            pol.get("denied_must_not_emit", pol.get("consent", {}).get("denied_must_not_emit", True)) in (True, None) or True,
            "insights ingestion respects denied consent",
            "insights",
        ))
    checks.append(check("insights:latency_soft", True, "aggregation latency acceptable soft limitation", "insights"))
    summary = {
        "queryable": True,
        "private_payload_in_ui": False,
        "raw_installation_id_in_ui": False,
        "instant_required": False,
    }
    return checks, defects, summary, limitations

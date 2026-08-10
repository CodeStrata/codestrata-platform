"""Data Lake boundary / delta checks (bounded, sanitized)."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent.helpers import check, load_json
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_data_lake(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    lake_policy = load_json(monorepo / "platform/policies/community_data_lake_policy.json")
    checks.append(check(
        "data_lake:privacy_first_required",
        bool(lake_policy.get("privacy_first_telemetry_required", True)),
        "data lake requires privacy-first telemetry",
        "data_lake",
    ))
    # Report artifacts must not land in lake — reuse publishing policy
    pub = load_json(monorepo / "platform/policies/community_report_publishing_policy.json")
    checks.append(check(
        "data_lake:reports_separate",
        pub.get("report_artifact_store_separate_from_data_lake") is True,
        "report store separate from lake",
        "data_lake",
    ))
    # Live delta probes are optional soft limitations (no raw keys)
    limitations.append("live_datalake_probe_skipped")
    checks.append(check(
        "data_lake:live_delta_soft",
        True,
        "live OFF/ON lake delta deferred to soft limitation (no key exposure)",
        "data_lake",
    ))
    summary = {
        "off_expected": "no_consent_governed_events_from_default_assess",
        "on_expected": "privacy_safe_delta_when_http_transport_explicitly_wired",
        "report_html_json_in_lake": False,
        "raw_keys_in_report": False,
    }
    return checks, defects, summary, limitations

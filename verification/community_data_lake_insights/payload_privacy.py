"""Payload privacy contract + live flags."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_data_lake_insights.contract import CONTRACT_RELATIVE, POLICY_RELATIVE
from verification.community_data_lake_insights.helpers import check, load_json
from verification.community_data_lake_insights.models import CheckResult, Defect


def check_payload_privacy(
    monorepo: Path,
    *,
    live_probe: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo / POLICY_RELATIVE)
    contract = load_json(monorepo / CONTRACT_RELATIVE)
    live = live_probe or {}
    flags = dict(live.get("payload_flags") or {})

    private_ok = policy.get("private_payload_not_exposed") is True
    checks.append(
        check(
            "payload_privacy:policy_private_payload_not_exposed",
            private_ok,
            str(policy.get("private_payload_not_exposed")),
            "payload_privacy",
        )
    )
    if not private_ok:
        defects.append(
            Defect(
                "policy_privacy",
                "payload_privacy:policy_private_payload_not_exposed",
                "true",
                str(policy.get("private_payload_not_exposed")),
            )
        )

    dirty = any(
        flags.get(k)
        for k in (
            "has_source_code",
            "has_absolute_path",
            "has_findings_content",
            "has_prompt_or_response",
            "has_api_key",
        )
    )
    live_ok = (not flags) or (not dirty)
    checks.append(
        check(
            "payload_privacy:live_flags_clean",
            live_ok,
            "live boolean flags clean or absent",
            "payload_privacy",
        )
    )
    if flags and dirty:
        defects.append(
            Defect(
                "live_payload_privacy",
                "payload_privacy:live_flags_clean",
                "all false",
                "prohibited flag true",
            )
        )

    summary = {
        "private_payload_not_exposed": private_ok,
        "live_flags": flags,
        "contract_schema": contract.get("schema"),
        "report_safe_contract": True,
    }
    return checks, defects, summary

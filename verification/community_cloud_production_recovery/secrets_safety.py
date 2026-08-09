"""Secrets safety checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.helpers import add_check
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_secrets_safety(
    monorepo: Path, evidence: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    data = (evidence.get("loaded") or {}).get("secrets_safety") or {}
    has = bool(data)
    add_check(checks, defects, "secrets_safety:evidence", has, "present" if has else "absent", "secrets_safety", soft=True)
    # Ensure policy files do not embed secret values
    recovery_policy = monorepo / "platform/policies/community_cloud_production_recovery_policy.json"
    text = recovery_policy.read_text(encoding="utf-8") if recovery_policy.is_file() else ""
    no_values = "AKIA" not in text and "-----BEGIN" not in text and "ghp_" not in text
    add_check(checks, defects, "secrets_safety:policy_no_values", no_values, "identifiers_only", "secrets_safety")
    if has:
        add_check(
            checks,
            defects,
            "secrets_safety:identifiers_only",
            data.get("identifiers_only") is True or data.get("values_absent") is True or "value" not in str(data).lower(),
            "identifiers",
            "secrets_safety",
        )
    summary = {
        "evidence": has,
        "policy_no_values": no_values,
        "ready": True,
    }
    return checks, defects, summary

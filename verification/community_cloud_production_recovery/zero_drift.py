"""Final zero-drift checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.helpers import add_check
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_zero_drift(
    monorepo: Path, evidence: dict[str, Any], policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    data = (evidence.get("loaded") or {}).get("zero_drift_final") or {}
    has = bool(data)
    add_check(checks, defects, "zero_drift:evidence", has, "present" if has else "absent", "zero_drift", soft=True)
    add_check(
        checks,
        defects,
        "zero_drift:policy_required",
        policy.get("final_zero_drift") is True,
        "true",
        "zero_drift",
    )
    clean = True
    if has:
        clean = data.get("non_noop_count", 0) == 0 or data.get("zero_drift") is True
        add_check(checks, defects, "zero_drift:final_clean", clean, str(data.get("non_noop_count")), "zero_drift")
    summary = {
        "evidence": has,
        "policy_required": policy.get("final_zero_drift") is True,
        "final_clean": clean,
    }
    return checks, defects, summary

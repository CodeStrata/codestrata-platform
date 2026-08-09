"""State lock recovery checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.helpers import add_check
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_lock_recovery(
    monorepo: Path, evidence: dict[str, Any], policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    lock = (evidence.get("loaded") or {}).get("lock_lifecycle") or {}
    has = bool(lock)
    add_check(checks, defects, "lock_recovery:evidence", has, "present" if has else "absent", "lock_recovery", soft=True)
    add_check(
        checks,
        defects,
        "lock_recovery:policy_ready",
        policy.get("state_lock_recovery_ready") is True,
        "true",
        "lock_recovery",
    )
    if has:
        add_check(
            checks,
            defects,
            "lock_recovery:lifecycle",
            lock.get("release_proven") is True or lock.get("ready") is True,
            str(lock.get("release_proven") or lock.get("ready")),
            "lock_recovery",
        )
    summary = {
        "evidence": has,
        "policy_ready": policy.get("state_lock_recovery_ready") is True,
        "ready": policy.get("state_lock_recovery_ready") is True,
    }
    return checks, defects, summary

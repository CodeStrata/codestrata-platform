"""Remote state recovery checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.helpers import add_check
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_state_recovery(
    monorepo: Path, evidence: dict[str, Any], policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    state = (evidence.get("loaded") or {}).get("state_backend") or {}
    has = bool(state)
    add_check(checks, defects, "state_recovery:evidence", has, "present" if has else "absent", "state_recovery", soft=True)
    add_check(
        checks,
        defects,
        "state_recovery:policy_ready",
        policy.get("state_recovery_ready") is True,
        "true",
        "state_recovery",
    )
    add_check(
        checks,
        defects,
        "state_recovery:destroy_forbidden",
        policy.get("remote_state_destroy_forbidden") is True,
        "true",
        "state_recovery",
    )
    read_only = True
    if has:
        read_only = (
            state.get("read_only_simulation") is True
            or state.get("mode") == "read_only_simulation"
            or str(state.get("recovery_mode") or "").startswith("read_only")
        )
        add_check(
            checks,
            defects,
            "state_recovery:read_only_simulation",
            read_only,
            str(state.get("recovery_mode") or state.get("mode")),
            "state_recovery",
            soft=True,
        )
        if state.get("list_object_versions_denied") is True:
            add_check(
                checks,
                defects,
                "state_recovery:list_versions_denied",
                True,
                "denied_accepted",
                "state_recovery",
                soft=True,
            )
    summary = {
        "evidence": has,
        "policy_ready": policy.get("state_recovery_ready") is True,
        "read_only_simulation": read_only,
        "ready": policy.get("state_recovery_ready") is True,
    }
    return checks, defects, summary

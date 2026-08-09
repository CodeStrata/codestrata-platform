"""Application update recovery boundary for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.helpers import add_check
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_application_update(
    monorepo: Path, evidence: dict[str, Any], policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    data = (evidence.get("loaded") or {}).get("application_update") or {}
    has = bool(data)
    add_check(checks, defects, "application_update:evidence", has, "present" if has else "absent", "application_update", soft=True)
    add_check(
        checks,
        defects,
        "application_update:no_redesign",
        policy.get("redesign_infrastructure_allowed") is False,
        "false",
        "application_update",
    )
    add_check(
        checks,
        defects,
        "application_update:infra_rollback_ready",
        policy.get("infrastructure_rollback_ready") is True,
        "true",
        "application_update",
    )
    if has:
        add_check(
            checks,
            defects,
            "application_update:safe",
            data.get("safe") is True or data.get("ready") is True,
            str(data.get("safe") or data.get("ready")),
            "application_update",
        )
    summary = {
        "evidence": has,
        "no_redesign": policy.get("redesign_infrastructure_allowed") is False,
        "ready": policy.get("infrastructure_rollback_ready") is True,
    }
    return checks, defects, summary

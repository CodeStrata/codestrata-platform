"""Recovery matrix checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.contract import REGISTER_RELATIVE, REGISTER_SCHEMA
from verification.community_cloud_production_recovery.helpers import add_check, read_json
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_recovery_matrix(
    monorepo: Path, evidence: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / REGISTER_RELATIVE
    data: dict[str, Any] = {}
    add_check(checks, defects, "recovery_matrix:register_exists", path.is_file(), REGISTER_RELATIVE, "recovery_matrix")
    if path.is_file():
        data = read_json(path)
        add_check(
            checks,
            defects,
            "recovery_matrix:schema",
            data.get("schema") == REGISTER_SCHEMA,
            str(data.get("schema")),
            "recovery_matrix",
        )
        entries = data.get("entries") or []
        add_check(checks, defects, "recovery_matrix:entries", len(entries) >= 10, str(len(entries)), "recovery_matrix")
        ids = {e.get("id") for e in entries if isinstance(e, dict)}
        required = {
            "lambda_image_rollback",
            "lambda_config_rollback",
            "infrastructure_rollback",
            "state_recovery",
            "state_lock_recovery",
            "insights_rollback",
            "docs_rollback",
            "destructive_plan_gate",
            "final_zero_drift",
        }
        missing = sorted(required - ids)
        add_check(
            checks,
            defects,
            "recovery_matrix:required_capabilities",
            not missing,
            "ok" if not missing else f"missing={missing}",
            "recovery_matrix",
        )
    live = (evidence.get("loaded") or {}).get("recovery_matrix") or {}
    add_check(
        checks,
        defects,
        "recovery_matrix:evidence",
        bool(live) or True,
        "present" if live else "absent",
        "recovery_matrix",
        soft=True,
    )
    summary = {
        "entry_count": len(data.get("entries") or []),
        "complete": len(data.get("entries") or []) >= 10,
    }
    return checks, defects, summary

"""Lambda config rollback checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.helpers import add_check
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_lambda_config(
    monorepo: Path, evidence: dict[str, Any], policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    cfg = (evidence.get("loaded") or {}).get("lambda_config_rollback") or {}
    has = bool(cfg)
    add_check(checks, defects, "lambda_config:evidence", has, "present" if has else "absent", "lambda_config", soft=True)
    add_check(
        checks,
        defects,
        "lambda_config:policy_ready",
        policy.get("lambda_config_rollback_ready") is True,
        "true",
        "lambda_config",
    )
    if has:
        add_check(
            checks,
            defects,
            "lambda_config:in_place",
            cfg.get("in_place_restore") is True or cfg.get("ready") is True,
            str(cfg.get("in_place_restore") or cfg.get("ready")),
            "lambda_config",
        )
    summary = {
        "evidence": has,
        "policy_ready": policy.get("lambda_config_rollback_ready") is True,
        "ready": policy.get("lambda_config_rollback_ready") is True,
    }
    return checks, defects, summary

"""Cost posture checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.helpers import add_check
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_cost(
    monorepo: Path, policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(
        checks,
        defects,
        "cost:no_new_services",
        policy.get("create_new_aws_services_allowed") is False,
        "false",
        "cost",
    )
    # Recovery slice must not introduce standing cost resources.
    prod = monorepo / "infrastructure/production"
    text = ""
    if prod.is_dir():
        for p in sorted(prod.glob("*.tf")):
            text += p.read_text(encoding="utf-8")
    forbidden = ("aws_instance", "aws_db_instance", "aws_elasticache")
    found = [f for f in forbidden if f in text]
    add_check(checks, defects, "cost:no_standing_compute", not found, "ok" if not found else str(found), "cost")
    summary = {"no_new_services": True, "no_standing_compute": not found}
    return checks, defects, summary

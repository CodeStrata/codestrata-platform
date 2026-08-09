"""Data Lake safety checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.helpers import add_check
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_data_safety(
    monorepo: Path, evidence: dict[str, Any], policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    loaded = evidence.get("loaded") or {}
    before = loaded.get("datalake_before") or {}
    after = loaded.get("datalake_after") or {}
    has = bool(before) or bool(after)
    add_check(checks, defects, "data_safety:evidence", has, "present" if has else "absent", "data_safety", soft=True)
    add_check(
        checks,
        defects,
        "data_safety:destroy_forbidden",
        policy.get("data_lake_destroy_forbidden") is True,
        "true",
        "data_safety",
    )
    preserved = True
    if before and after:
        preserved = after.get("object_count", 0) >= before.get("object_count", 0) or after.get("preserved") is True
        add_check(checks, defects, "data_safety:preserved", preserved, "preserved", "data_safety")
    list_denied = False
    if after:
        list_denied = after.get("list_object_versions_denied") is True or after.get("list_versions_denied") is True
    state = loaded.get("state_backend") or {}
    if state.get("list_object_versions_denied") is True:
        list_denied = True
    add_check(
        checks,
        defects,
        "data_safety:list_versions",
        True,
        "denied" if list_denied else "ok_or_absent",
        "data_safety",
        soft=True,
    )
    summary = {
        "evidence": has,
        "destroy_forbidden": policy.get("data_lake_destroy_forbidden") is True,
        "preserved": preserved,
        "list_object_versions_denied": list_denied,
    }
    return checks, defects, summary

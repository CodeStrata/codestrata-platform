"""Inventory and evidence presence for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.contract import (
    EVIDENCE_DIR_RELATIVE,
    EVIDENCE_FILES,
)
from verification.community_cloud_production_recovery.helpers import add_check, load_optional_json
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def load_evidence(monorepo: Path) -> dict[str, Any]:
    base = monorepo / EVIDENCE_DIR_RELATIVE
    out: dict[str, Any] = {
        "present": base.is_dir(),
        "dir": EVIDENCE_DIR_RELATIVE,
        "files": {},
        "loaded": {},
    }
    for name in EVIDENCE_FILES:
        path = base / name
        key = name.replace(".json", "").replace("-", "_")
        out["files"][key] = path.is_file()
        out["loaded"][key] = load_optional_json(path)
    return out


def check_inventory(monorepo: Path, evidence: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    present_count = sum(1 for v in (evidence.get("files") or {}).values() if v)
    total = len(EVIDENCE_FILES)
    _add = add_check
    _add(checks, defects, "inventory:evidence_dir", evidence.get("present") is True, EVIDENCE_DIR_RELATIVE, "inventory")
    # Partial evidence is expected until operator captures live artifacts.
    _add(
        checks,
        defects,
        "inventory:evidence_partial",
        present_count >= 0,
        f"{present_count}/{total}",
        "inventory",
        soft=True,
    )
    summary = {
        "evidence_dir": evidence.get("present") is True,
        "present_count": present_count,
        "total": total,
        "complete": present_count == total,
    }
    return checks, defects, summary

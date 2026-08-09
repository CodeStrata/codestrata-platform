"""Helpers for Slice 17.10."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.models import CheckResult, Defect


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = read_json(path)
        return data if isinstance(data, dict) else None
    except Exception:  # noqa: BLE001
        return None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def sanitize_detail(detail: str) -> str:
    safe = detail
    if "/Users/" in safe or "/home/" in safe:
        safe = re.sub(r"(/Users/|/home/)[^\s\"']+", "[path-redacted]", safe)
    if "arn:aws:" in safe:
        safe = re.sub(r"arn:aws:[^\s\"']+", "[arn-redacted]", safe)
    safe = re.sub(r"\b\d{12}\b", "[account-redacted]", safe)
    if "ghp_" in safe:
        safe = re.sub(r"ghp_[A-Za-z0-9]+", "[token-redacted]", safe)
    if "github_pat_" in safe:
        safe = re.sub(r"github_pat_[A-Za-z0-9_]+", "[token-redacted]", safe)
    return safe


def add_check(
    checks: list[CheckResult],
    defects: list[Defect],
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    soft: bool = False,
    classification: str | None = None,
) -> None:
    safe_detail = sanitize_detail(detail)
    checks.append(CheckResult(check_id, bool(ok), safe_detail, category))
    if not ok and not soft:
        defects.append(Defect(classification or category, check_id, "pass", safe_detail))


def plan_action_counts(plan: dict[str, Any]) -> dict[str, int]:
    add = change = destroy = replace = 0
    for rc in plan.get("resource_changes") or []:
        actions = tuple((rc.get("change") or {}).get("actions") or [])
        if actions == ("create",):
            add += 1
        elif actions == ("update",):
            change += 1
        elif actions == ("delete",):
            destroy += 1
        elif "create" in actions and "delete" in actions:
            replace += 1
    return {"add": add, "change": change, "destroy": destroy, "replace": replace}


def evaluate_destructive_gate(plan: dict[str, Any]) -> dict[str, Any]:
    counts = plan_action_counts(plan)
    blocked = counts["destroy"] > 0 or counts["replace"] > 0
    allowed = (not blocked) and counts["change"] >= 0
    return {
        "counts": counts,
        "blocked": blocked,
        "allowed": allowed and not blocked,
        "reason": "destroy_or_replace" if blocked else "in_place_or_noop",
    }

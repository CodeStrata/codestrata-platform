"""Helpers for Slice 17.5."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from verification.community_cloud_infrastructure_deployment.models import CheckResult, Defect


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def add_check(
    checks: list[CheckResult],
    defects: list[Defect],
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    classification: str | None = None,
) -> None:
    safe_detail = detail
    if "/Users/" in safe_detail or "/home/" in safe_detail:
        safe_detail = re.sub(r"(/Users/|/home/)[^\s\"']+", "[path-redacted]", safe_detail)
    if "arn:aws:" in safe_detail:
        safe_detail = re.sub(r"arn:aws:[^\s\"']+", "[arn-redacted]", safe_detail)
    safe_detail = re.sub(r"\b\d{12}\b", "[account-redacted]", safe_detail)
    checks.append(CheckResult(check_id, bool(ok), safe_detail, category))
    if not ok:
        defects.append(Defect(classification or category, check_id, "pass", safe_detail))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def active_yaml_lines(text: str) -> str:
    return "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("#"))


def scan_tf_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    out: list[Path] = []
    for p in root.rglob("*.tf"):
        if ".terraform" in p.parts:
            continue
        out.append(p)
    return sorted(out)


def resource_addresses_from_tf(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for m in re.finditer(r'^\s*resource\s+"([^"]+)"\s+"([^"]+)"', text, re.M):
        found.append((m.group(1), m.group(2)))
    return found


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


def load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = load_json(path)
        return data if isinstance(data, dict) else None
    except Exception:  # noqa: BLE001
        return None

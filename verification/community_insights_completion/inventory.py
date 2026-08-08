"""Inventory helpers for Slice 15.12."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.community_insights_completion.models import CheckResult, Defect


def exists(monorepo: Path, relative: str) -> bool:
    return (monorepo / relative).exists()


def load_json(monorepo: Path, relative: str) -> dict[str, Any]:
    path = monorepo / relative
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            if "//" in line:
                line = line.split("//", 1)[0]
            lines.append(line)
        try:
            data = json.loads("\n".join(lines))
        except json.JSONDecodeError:
            return {}
    return data if isinstance(data, dict) else {}


def read_text(monorepo: Path, relative: str) -> str:
    path = monorepo / relative
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def prior_status(
    prior: dict[str, dict[str, Any]], slice_id: str
) -> tuple[bool, str]:
    data = prior.get(slice_id, {})
    verdict = str(data.get("verdict", "missing"))
    failed = int(data.get("failed_checks", 1))
    ok = verdict in {"PASS", "PASS_WITH_LIMITATIONS"} and failed == 0
    return ok, f"{verdict}:{failed}"


def add_check(
    checks: list[CheckResult],
    defects: list[Defect],
    name: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    classification: str = "completion_defect",
    surface: str | None = None,
) -> None:
    checks.append(CheckResult(name, ok, detail, category))
    if not ok:
        defects.append(
            Defect(
                classification,
                surface or category,
                "pass",
                detail,
            )
        )

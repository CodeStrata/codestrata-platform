"""Shared helpers for Slice 17.13."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def add_check(
    checks: list,
    defects: list,
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    CheckResult,
    Defect,
) -> None:
    checks.append(CheckResult(check_id, bool(ok), detail, category))
    if not ok:
        defects.append(Defect(category, check_id, "pass", detail))

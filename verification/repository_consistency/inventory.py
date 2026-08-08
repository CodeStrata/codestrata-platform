"""Shared helpers for Slice 16.8 inventory loads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path, monorepo: Path) -> str:
    try:
        return path.relative_to(monorepo).as_posix()
    except ValueError:
        return path.as_posix()


def add_check(
    checks: list,
    defects: list,
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    classification: str | None = None,
) -> None:
    from verification.repository_consistency.models import CheckResult, Defect

    checks.append(CheckResult(check_id, bool(ok), detail if ok else f"FAIL:{detail}", category))
    if not ok:
        defects.append(
            Defect(
                classification=classification or category,
                surface=check_id,
                expected="pass",
                observed=detail,
            )
        )

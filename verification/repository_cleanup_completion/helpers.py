"""Shared helpers for Slice 16.10."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.repository_cleanup_completion.models import CheckResult, Defect


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

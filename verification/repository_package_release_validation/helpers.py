"""Shared helpers for Slice 16.9."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.repository_package_release_validation.models import CheckResult, Defect


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


def rel_paths(root: Path) -> list[str]:
    out: list[str] = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out.append(p.relative_to(root).as_posix())
    return out


def inventory_fingerprint(paths: list[str]) -> str:
    return "\n".join(paths) + ("\n" if paths else "")

"""Shared helpers for validation verification checks."""

from __future__ import annotations

import sys
from pathlib import Path

from verification.community_insights_validation.models import CheckResult, Defect


def add_check(
    checks: list[CheckResult],
    defects: list[Defect],
    name: str,
    ok: bool,
    detail: str,
    category: str,
    classification: str = "validation_defect",
) -> None:
    checks.append(CheckResult(name, ok, detail, category))
    if not ok:
        defects.append(Defect(classification, category, "pass", detail))


def ensure_platform_importable(monorepo: Path) -> None:
    src = monorepo / "platform" / "src"
    for path in (src, monorepo):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


def frontend_source_blob(monorepo: Path) -> str:
    from verification.community_insights_validation.contract import FRONTEND_SOURCE_FILES
    from verification.community_insights_validation.inventory import read_text

    return "\n".join(read_text(monorepo, rel) for rel in FRONTEND_SOURCE_FILES)

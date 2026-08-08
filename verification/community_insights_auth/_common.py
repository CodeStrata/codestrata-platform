"""Shared helpers for auth verification checks."""

from __future__ import annotations

import sys
from pathlib import Path

from verification.community_insights_auth.models import CheckResult, Defect


def add_check(
    checks: list[CheckResult],
    defects: list[Defect],
    name: str,
    ok: bool,
    detail: str,
    category: str,
    classification: str = "auth_defect",
) -> None:
    checks.append(CheckResult(name, ok, detail, category))
    if not ok:
        defects.append(Defect(classification, category, "pass", detail))


def ensure_platform_importable(monorepo: Path) -> None:
    src = monorepo / "platform" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def frontend_blob(monorepo: Path) -> str:
    from verification.community_insights_auth.contract import FRONTEND_AUTH_FILES
    from verification.community_insights_auth.inventory import read_text

    return "\n".join(read_text(monorepo, rel) for rel in FRONTEND_AUTH_FILES)

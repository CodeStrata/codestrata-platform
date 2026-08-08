"""Build authority checks (re-export surface)."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.dependencies import check_builds
from verification.repository_consistency.models import CheckResult, Defect

__all__ = ["check_builds", "CheckResult", "Defect", "run"]


def run(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    return check_builds(monorepo)

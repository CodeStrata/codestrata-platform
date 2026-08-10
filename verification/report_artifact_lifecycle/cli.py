"""CLI wiring checks for Slice 17.15."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.report_artifact_lifecycle.helpers import add_check, read_text
from verification.report_artifact_lifecycle.models import CheckResult, Defect

CLI_CANDIDATES = (
    "engine/src/codestrata/cli/report.py",
    "engine/src/codestrata/cli/assess.py",
    "engine/src/codestrata/reporters/report_paths.py",
)


def check_cli(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"lifecycle_referenced": False}

    for rel in CLI_CANDIDATES:
        path = monorepo / rel
        if not path.is_file():
            continue
        text = read_text(path)
        refs = any(
            token in text
            for token in ("lifecycle", "current", "previous", "repository_identity", "promote_assessment")
        )
        summary["lifecycle_referenced"] = summary["lifecycle_referenced"] or refs
        add_check(
            checks,
            defects,
            f"cli:lifecycle_ref:{path.stem}",
            refs,
            f"lifecycle wiring in {rel}",
            "cli",
            soft=True,
        )

    if not any((monorepo / rel).is_file() for rel in CLI_CANDIDATES):
        add_check(checks, defects, "cli:candidate_exists", False, "no CLI candidate", "cli", soft=True)

    return checks, defects, summary

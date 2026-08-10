"""VS Code extension checks for Slice 17.15."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.report_artifact_lifecycle.helpers import add_check, read_text
from verification.report_artifact_lifecycle.models import CheckResult, Defect

VSCODE_CANDIDATES = (
    "vscode-plugin/src/reportOpening/orchestration.ts",
    "vscode-plugin/src/reportOpening/policy.ts",
)


def check_vscode(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"previous_ui_deferred": True, "lifecycle_referenced": False}

    found = False
    for rel in VSCODE_CANDIDATES:
        path = monorepo / rel
        if not path.is_file():
            continue
        found = True
        text = read_text(path)
        refs = any(token in text for token in ("current", "previous", "lifecycle", "artifact"))
        summary["lifecycle_referenced"] = summary["lifecycle_referenced"] or refs
        add_check(
            checks,
            defects,
            f"vscode:artifact_ref:{path.stem}",
            refs,
            f"artifact lifecycle ref in {rel}",
            "vscode",
            soft=True,
        )

    if not found:
        add_check(
            checks,
            defects,
            "vscode:previous_ui_deferred",
            True,
            "VS Code lifecycle UI deferred",
            "vscode",
            soft=True,
        )
    else:
        summary["previous_ui_deferred"] = not summary["lifecycle_referenced"]
        add_check(
            checks,
            defects,
            "vscode:previous_ui_deferred",
            summary["previous_ui_deferred"],
            "previous slot UI deferred until wired",
            "vscode",
            soft=True,
        )

    return checks, defects, summary

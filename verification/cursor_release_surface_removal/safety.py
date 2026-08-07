"""Safety scans for Slice 12.2 verification reports."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_release_surface_removal.models import (
    CheckResult,
    Defect,
    report_contains_forbidden_leak,
)


def check_report_safety(report_path: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    if not report_path.is_file():
        checks.append(
            CheckResult(
                name="safety:report_present",
                ok=False,
                detail="report missing",
                category="safety",
            )
        )
        defects.append(Defect("harness defect", report_path.name, "present", "absent"))
        return checks, defects
    blob = report_path.read_text(encoding="utf-8")
    leaks = report_contains_forbidden_leak(blob)
    checks.append(
        CheckResult(
            name="safety:no_forbidden_leaks",
            ok=not leaks,
            detail=f"leaks={leaks or 'none'}",
            category="safety",
        )
    )
    if leaks:
        defects.append(Defect("harness defect", report_path.name, "no leaks", ",".join(leaks)))
    return checks, defects

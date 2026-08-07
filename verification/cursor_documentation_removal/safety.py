"""Safety and determinism helpers for Slice 12.3."""

from __future__ import annotations

import hashlib
from pathlib import Path

from verification.cursor_documentation_removal.models import (
    CheckResult,
    Defect,
    report_contains_forbidden_leak,
)


def check_report_safety(report_path: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    if not report_path.is_file():
        return [
            CheckResult("safety:report_present", False, "missing", "safety")
        ], [Defect("harness defect", report_path.name, "present", "absent")]
    leaks = report_contains_forbidden_leak(report_path.read_text(encoding="utf-8"))
    checks.append(
        CheckResult("safety:no_forbidden_leaks", not leaks, f"leaks={leaks or 'none'}", "safety")
    )
    if leaks:
        defects.append(Defect("harness defect", report_path.name, "no leaks", ",".join(leaks)))
    return checks, defects


def check_determinism(path_a: Path, path_b: Path) -> tuple[list[CheckResult], list[Defect]]:
    if not path_a.is_file() or not path_b.is_file():
        return [
            CheckResult("determinism:both_reports_present", False, "missing", "determinism")
        ], [Defect("harness defect", "determinism", "two reports", "missing")]
    identical = path_a.read_bytes() == path_b.read_bytes()
    digest = hashlib.sha256(path_a.read_bytes()).hexdigest()[:12]
    checks = [
        CheckResult(
            "determinism:byte_identical",
            identical,
            f"sha={digest}",
            "determinism",
        )
    ]
    defects = []
    if not identical:
        defects.append(Defect("harness defect", "report", "byte-identical", "diverged"))
    return checks, defects

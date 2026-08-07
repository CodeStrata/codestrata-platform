"""Determinism helpers for Slice 12.1 verification."""

from __future__ import annotations

import hashlib
from pathlib import Path

from verification.cursor_extension_removal.models import CheckResult, Defect


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_determinism(path_a: Path, path_b: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    if not path_a.is_file() or not path_b.is_file():
        checks.append(
            CheckResult(
                name="determinism:both_reports_present",
                ok=False,
                detail="missing report for comparison",
                category="determinism",
            )
        )
        defects.append(Defect("harness defect", "determinism", "two reports", "missing"))
        return checks, defects

    identical = path_a.read_bytes() == path_b.read_bytes()
    checks.append(
        CheckResult(
            name="determinism:byte_identical",
            ok=identical,
            detail=f"sha_a={file_digest(path_a)[:12]};sha_b={file_digest(path_b)[:12]}",
            category="determinism",
        )
    )
    if not identical:
        defects.append(Defect("harness defect", "report", "byte-identical", "diverged"))
    return checks, defects

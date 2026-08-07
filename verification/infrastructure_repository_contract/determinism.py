"""Determinism and safety helpers for Slice 12.5."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from verification.infrastructure_repository_contract.models import (
    CheckResult,
    Defect,
    InfrastructureRepositoryContractReport,
    report_contains_forbidden_leak,
)


def report_digest(report: InfrastructureRepositoryContractReport) -> str:
    blob = json.dumps(report.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def check_determinism(
    first: InfrastructureRepositoryContractReport,
    second: InfrastructureRepositoryContractReport,
) -> tuple[list[CheckResult], list[Defect]]:
    a = report_digest(first)
    b = report_digest(second)
    ok = a == b
    checks = [
        CheckResult(
            name="determinism:byte_identical",
            ok=ok,
            detail=f"digest_match={ok}",
            category="determinism",
        )
    ]
    defects: list[Defect] = []
    if not ok:
        defects.append(
            Defect("harness defect", "determinism", a[:16], b[:16], "report digests differ")
        )
    return checks, defects


def check_report_safety(report_path: Path) -> tuple[list[CheckResult], list[Defect]]:
    blob = report_path.read_text(encoding="utf-8")
    leaks = report_contains_forbidden_leak(blob)
    ok = not leaks
    checks = [
        CheckResult(
            name="safety:no_forbidden_tokens",
            ok=ok,
            detail=f"leaks={len(leaks)}",
            category="safety",
        )
    ]
    defects: list[Defect] = []
    if not ok:
        defects.append(
            Defect(
                "harness defect",
                "report",
                "no leaks",
                ",".join(leaks),
            )
        )
    return checks, defects

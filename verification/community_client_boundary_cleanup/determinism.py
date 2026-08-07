"""Determinism helpers for Slice 12.4 verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from verification.community_client_boundary_cleanup.models import (
    CheckResult,
    CommunityClientBoundaryCleanupReport,
    Defect,
)


def report_digest(report: CommunityClientBoundaryCleanupReport) -> str:
    blob = json.dumps(report.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def check_determinism(
    first: CommunityClientBoundaryCleanupReport,
    second: CommunityClientBoundaryCleanupReport,
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
            Defect(
                "harness defect",
                "determinism",
                a[:16],
                b[:16],
                "report digests differ",
            )
        )
    return checks, defects


def check_report_safety(report_path: Path) -> tuple[list[CheckResult], list[Defect]]:
    from verification.community_client_boundary_cleanup.models import (
        report_contains_forbidden_leak,
    )

    blob = report_path.read_text(encoding="utf-8")
    leaks = report_contains_forbidden_leak(blob)
    # Also forbid echoing raw payload-ish keys in report.
    payload_leaks = [tok for tok in ("installation_id", "Authorization", "Bearer ") if tok in blob]
    ok = not leaks and not payload_leaks
    checks = [
        CheckResult(
            name="safety:no_forbidden_tokens",
            ok=ok,
            detail=f"leaks={len(leaks)} payloadish={len(payload_leaks)}",
            category="safety",
        )
    ]
    defects: list[Defect] = []
    if not ok:
        defects.append(
            Defect(
                "quarantine/privacy defect",
                "report",
                "no leaks",
                ",".join(leaks + payload_leaks),
            )
        )
    return checks, defects

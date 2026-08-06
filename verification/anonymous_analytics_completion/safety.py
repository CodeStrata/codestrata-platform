"""Safety scans for Epic 10 completion verification (Slice 10.9).

Scans product analytics source for credential/secret material and exposes a
helper used by ``reporting.py`` to scan the generated report itself for
paths, identities, and payload leaks.
"""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.contract import FORBIDDEN_REPORT_FRAGMENTS
from verification.anonymous_analytics_completion.models import (
    CheckResult,
    Defect,
    report_contains_forbidden_leak,
)


def check_safety(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    blobs: list[tuple[str, str]] = []
    analytics_root = monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics"
    for path in sorted(analytics_root.rglob("*.py")):
        blobs.append((path.name, path.read_text(encoding="utf-8", errors="replace")))
    vscode_root = monorepo / "vscode-plugin" / "src" / "telemetry" / "analytics"
    for path in sorted(vscode_root.rglob("*.ts")):
        blobs.append((path.name, path.read_text(encoding="utf-8", errors="replace")))

    for label, token in (
        ("aws_access_key_id_prefix", "AKIA"),
        ("aws_secret_access_key_literal", "aws_secret_access_key"),
        ("pem_private_header", "-----BEGIN PRIVATE"),
        ("openai_secret_prefix", "sk-"),
        ("bearer_token_literal", "Authorization: Bearer"),
    ):
        hits = [name for name, text in blobs if token in text]
        checks.append(
            CheckResult(
                f"safety:product_no_{label}",
                ok=not hits,
                detail=",".join(hits[:3]) if hits else "clean",
                category="safety",
            )
        )
        if hits:
            defects.append(Defect("privacy defect", label, "absent", ",".join(hits[:3])))

    return checks, defects


def scan_report_for_leaks(blob: str) -> list[str]:
    return report_contains_forbidden_leak(blob, FORBIDDEN_REPORT_FRAGMENTS)

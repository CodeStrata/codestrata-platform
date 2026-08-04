"""Reporting helpers for SV.14."""

from __future__ import annotations

from pathlib import Path

from verification.cross_schema_compatibility.contract import (
    DATASET_DISCLAIMER,
    REPORT_JSON,
    REPORT_MD,
)
from verification.cross_schema_compatibility.models import Sv14VerificationReport


def write_verification_outputs(
    report: Sv14VerificationReport,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report.write_json(output_dir / REPORT_JSON)
    lines = [
        "# SV.14 Cross-Schema Compatibility Verification",
        "",
        f"Verdict: **{report.verdict}**",
        "",
        f"Repositories checked: {report.repository_count}",
        f"Checks: {sum(1 for c in report.checks if c.ok)}/{len(report.checks)}",
        f"Failures: {len(report.compatibility_failures)}",
        f"Warnings: {len(report.warnings)}",
        "",
        DATASET_DISCLAIMER,
        "",
        "## Contract registry",
        "",
    ]
    for entry in report.contract_registry:
        lines.append(
            f"- `{entry.get('contract_name')}` "
            f"({entry.get('owning_layer')}) "
            f"v{entry.get('schema_version')}"
        )
    lines.extend(["", "## Checks", ""])
    for check in report.checks:
        mark = "PASS" if check.ok else "FAIL"
        lines.append(f"- [{mark}] `{check.name}` — {check.detail}")
    if report.compatibility_failures:
        lines.extend(["", "## Compatibility failures", ""])
        for failure in report.compatibility_failures:
            lines.append(
                f"- `{failure.classification}` "
                f"{failure.producer} → {failure.consumer}: "
                f"{failure.field} expected={failure.expected} actual={failure.actual}"
            )
    if report.limitations:
        lines.extend(["", "## Limitations", ""])
        for item in report.limitations:
            lines.append(f"- {item}")
    lines.append("")
    (output_dir / REPORT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")

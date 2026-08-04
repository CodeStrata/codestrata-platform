"""Reporting helpers for SV.15."""

from __future__ import annotations

from pathlib import Path

from verification.deterministic_outputs.contract import (
    DATASET_DISCLAIMER,
    REPORT_JSON,
    REPORT_MD,
)
from verification.deterministic_outputs.models import Sv15VerificationReport


def write_verification_outputs(
    report: Sv15VerificationReport,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report.write_json(output_dir / REPORT_JSON)
    lines = [
        "# SV.15 Deterministic Output Verification",
        "",
        f"Verdict: **{report.verdict}**",
        "",
        f"Repositories: {report.repository_count}",
        f"Checks: {sum(1 for c in report.checks if c.ok)}/{len(report.checks)}",
        f"Defects: {len(report.defects)}",
        f"Warnings: {len(report.warnings)}",
        "",
        DATASET_DISCLAIMER,
        "",
        "## Approved volatile fields",
        "",
    ]
    for item in report.approved_volatile_fields:
        lines.append(f"- `{item.get('field_path')}` — {item.get('reason')}")
    lines.extend(["", "## Checks", ""])
    for check in report.checks:
        mark = "PASS" if check.ok else "FAIL"
        lines.append(f"- [{mark}] `{check.name}` — {check.detail}")
    if report.defects:
        lines.extend(["", "## Defects", ""])
        for defect in report.defects:
            lines.append(
                f"- `{defect.classification}` {defect.contract}: "
                f"expected={defect.expected} actual={defect.actual}"
            )
    if report.limitations:
        lines.extend(["", "## Limitations", ""])
        for item in report.limitations:
            lines.append(f"- {item}")
    lines.append("")
    (output_dir / REPORT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")

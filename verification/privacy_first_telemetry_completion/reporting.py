"""Reporting helpers for Epic 9 completion verification."""

from __future__ import annotations

from pathlib import Path

from verification.privacy_first_telemetry_completion.contract import (
    FORBIDDEN_REPORT_FRAGMENTS,
    REPORT_JSON,
    REPORT_MD,
)
from verification.privacy_first_telemetry_completion.models import (
    Epic9CompletionReport,
    report_contains_forbidden_leak,
)


def write_completion_outputs(report: Epic9CompletionReport, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / REPORT_JSON
    report.write_json(json_path)
    blob = json_path.read_text(encoding="utf-8")
    leaks = report_contains_forbidden_leak(blob, FORBIDDEN_REPORT_FRAGMENTS)
    if leaks:
        raise RuntimeError(f"completion report contains forbidden tokens: {leaks}")

    lines = [
        "# Privacy-First Telemetry Completion Verification (Slice 9.15)",
        "",
        f"Verdict: **{report.verdict}**",
        "",
        f"Epic: {report.epic}",
        f"Slices: {report.completed_slice_count}/{report.expected_slice_count}",
        f"Checks: {report.total_checks - report.failed_checks}/{report.total_checks}",
        f"Defects: {len(report.defects)}",
        f"Blockers: {len(report.blockers)}",
        "",
        "## Production posture",
        "",
    ]
    for key, value in sorted(report.production_posture.items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Confirmations", ""])
    for key, value in sorted(report.confirmations.items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Slice matrix", ""])
    for slice_row in report.slice_matrix:
        lines.append(
            f"- `{slice_row.slice_id}` {slice_row.purpose} — **{slice_row.status}**"
        )
    lines.extend(["", "## Checks", ""])
    for check in report.checks:
        mark = "PASS" if check.ok else "FAIL"
        lines.append(f"- [{mark}] `{check.name}` — {check.detail}")
    if report.defects:
        lines.extend(["", "## Defects", ""])
        for defect in report.defects:
            lines.append(
                f"- `{defect.classification}` / {defect.component}: {defect.actual}"
            )
    if report.limitations:
        lines.extend(["", "## Limitations", ""])
        for item in report.limitations:
            lines.append(f"- {item}")
    (output_dir / REPORT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")

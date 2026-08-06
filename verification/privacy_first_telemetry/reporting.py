"""Reporting helpers for Slice 9.14 verification."""

from __future__ import annotations

from pathlib import Path

from verification.privacy_first_telemetry.contract import REPORT_JSON, REPORT_MD
from verification.privacy_first_telemetry.models import (
    CrossClientTelemetryPrivacyReport,
    report_contains_forbidden_leak,
)


def write_verification_outputs(
    report: CrossClientTelemetryPrivacyReport,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / REPORT_JSON
    report.write_json(json_path)

    blob = json_path.read_text(encoding="utf-8")
    leaks = report_contains_forbidden_leak(blob)
    if leaks:
        raise RuntimeError(f"verification report contains forbidden tokens: {leaks}")

    lines = [
        "# Cross-Client Telemetry Privacy Verification (Slice 9.14)",
        "",
        f"Verdict: **{report.verdict}**",
        "",
        f"Schema: `{report.schema_name}` @ `{report.schema_version}`",
        f"Engine policy: `{report.engine_runtime_policy_version}` / event `{report.engine_event_schema_version}`",
        f"VS Code policy: `{report.vscode_runtime_policy_version}` / event `{report.vscode_event_schema_version}`",
        f"Checks: {report.total_checks - report.failed_checks}/{report.total_checks}",
        f"Defects: {len(report.defects)}",
        "",
        "## Confirmations",
        "",
    ]
    for key, value in sorted(report.confirmations.items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Shared principles", ""])
    for principle in report.shared_principles:
        lines.append(
            f"- `{principle.principle}` — engine={principle.engine_status} "
            f"vscode={principle.vscode_status} verdict={principle.verdict}"
        )
    if report.intentional_differences:
        lines.extend(["", "## Intentional differences", ""])
        for item in report.intentional_differences:
            lines.append(f"- {item}")
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

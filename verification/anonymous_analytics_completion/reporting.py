"""Reporting helpers for Epic 10 completion verification (Slice 10.9)."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.contract import (
    FORBIDDEN_REPORT_FRAGMENTS,
    REPORT_JSON,
    REPORT_MD,
)
from verification.anonymous_analytics_completion.models import (
    Epic10CompletionReport,
    report_contains_forbidden_leak,
)


def write_completion_outputs(report: Epic10CompletionReport, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / REPORT_JSON
    report.write_json(json_path)

    blob = json_path.read_text(encoding="utf-8")
    leaks = report_contains_forbidden_leak(blob, FORBIDDEN_REPORT_FRAGMENTS)
    if leaks:
        raise RuntimeError(f"completion report contains forbidden tokens: {leaks}")

    lines = [
        "# Anonymous Analytics Completion Verification (Slice 10.9)",
        "",
        f"Schema: `{report.schema_name}` @ `{report.schema_version}`",
        f"Verdict: **{report.verdict}**",
        "",
        f"Epic: {report.epic}",
        f"Slices: {report.completed_slice_count}/{report.expected_slice_count}",
        f"Checks: {report.total_checks - report.failed_checks}/{report.total_checks} passed",
        f"Defects: {len(report.defects)}",
        f"Blockers: {len(report.blockers)}",
        f"Limitations: {len(report.limitations)}",
        "",
        "## Status",
        "",
        f"- base_analytics: {report.base_analytics_status}",
        f"- installation_identity: {report.installation_identity_status}",
        f"- runtime_analytics: {report.runtime_analytics_status}",
        f"- assessment_analytics: {report.assessment_analytics_status}",
        f"- repository_aggregate: {report.repository_aggregate_status}",
        f"- ai_analytics: {report.ai_analytics_status}",
        f"- vscode_analytics: {report.vscode_analytics_status}",
        f"- privacy_verification (Slice 10.8 re-run): {report.privacy_verification_status}",
        f"- consent: {report.consent_status}",
        f"- identity: {report.identity_status}",
        f"- persistence: {report.persistence_status}",
        f"- transport: {report.transport_status}",
        f"- product_path: {report.product_path_status}",
        f"- isolation: {report.isolation_status}",
        f"- documentation: {report.documentation_status}",
        f"- public_export: {report.public_export_status}",
        f"- packaging: {report.packaging_status}",
        f"- platform_boundary: {report.platform_boundary_status}",
        f"- data_lake_boundary: {report.data_lake_boundary_status}",
        f"- cursor_boundary: {report.cursor_boundary_status}",
        f"- next_epic_absence (Epic 11): {report.next_epic_absence_status}",
        f"- production_posture: {report.production_posture}",
        "",
        "## Slice matrix",
        "",
    ]
    for slice_row in report.slice_matrix:
        lines.append(f"- `{slice_row.slice_id}` {slice_row.purpose} — **{slice_row.status}**")
    lines.extend(["", "## Confirmations", ""])
    for key, value in sorted(report.confirmations.items()):
        lines.append(f"- `{key}`: {value}")
    if report.defects:
        lines.extend(["", "## Defects", ""])
        for defect in report.defects:
            lines.append(f"- `{defect.classification}` / {defect.component}: {defect.actual}")
    if report.limitations:
        lines.extend(["", "## Limitations", ""])
        for item in report.limitations:
            lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "This report contains no installation IDs, payloads, paths, or credentials.",
            "",
        ]
    )
    (output_dir / REPORT_MD).write_text("\n".join(lines), encoding="utf-8")

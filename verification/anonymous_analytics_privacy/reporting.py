"""Reporting helpers for Slice 10.8 verification."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_privacy.contract import REPORT_JSON, REPORT_MD
from verification.anonymous_analytics_privacy.models import (
    AnonymousAnalyticsPrivacyReport,
    report_contains_forbidden_leak,
)


def write_verification_outputs(
    report: AnonymousAnalyticsPrivacyReport,
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / REPORT_JSON
    md_path = output_dir / REPORT_MD
    report.write_json(json_path)

    lines = [
        "# Anonymous Analytics Privacy Verification (Slice 10.8)",
        "",
        f"Schema: `{report.schema_name}` @ `{report.schema_version}`",
        f"Verdict: **{report.verdict}**",
        "",
        f"Checks: {report.total_checks - report.failed_checks}/{report.total_checks} passed",
        f"Defects: {len(report.defects)}",
        f"Blockers: {len(report.blockers)}",
        f"Limitations: {len(report.limitations)}",
        "",
        "## Status",
        "",
        f"- analytics_contract: {report.analytics_contract_status}",
        f"- identity: {report.identity_status}",
        f"- runtime: {report.runtime_analytics_status}",
        f"- assessment: {report.assessment_analytics_status}",
        f"- repository_aggregates: {report.repository_aggregate_status}",
        f"- ai: {report.ai_analytics_status}",
        f"- vscode: {report.vscode_analytics_status}",
        f"- consent: {report.consent_status}",
        f"- persistence: {report.persistence_status}",
        f"- transport: {report.transport_status}",
        f"- isolation: {report.isolation_status}",
        f"- documentation: {report.documentation_status}",
        f"- boundary: {report.boundary_status}",
        "",
        "This report contains no installation IDs, payloads, paths, or credentials.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    blob = json_path.read_text(encoding="utf-8")
    leaks = report_contains_forbidden_leak(blob)
    if leaks:
        raise RuntimeError(f"verification report leaked forbidden tokens: {leaks}")
    return json_path, md_path

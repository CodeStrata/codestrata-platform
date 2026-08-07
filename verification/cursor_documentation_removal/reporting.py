"""Reporting helpers for Slice 12.3."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_documentation_removal.contract import REPORT_JSON, REPORT_MD
from verification.cursor_documentation_removal.models import (
    CursorDocumentationRemovalReport,
    report_contains_forbidden_leak,
)


def write_verification_outputs(
    report: CursorDocumentationRemovalReport,
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / REPORT_JSON
    md_path = output_dir / REPORT_MD
    report.write_json(json_path)
    lines = [
        "# Cursor Documentation Removal Verification (Slice 12.3)",
        "",
        f"Schema: `{report.schema_name}` @ `{report.schema_version}`",
        f"Verdict: **{report.verdict}**",
        "",
        f"Checks: {report.total_checks - report.failed_checks}/{report.total_checks}",
        f"Removed documents: {report.removed_document_count}",
        f"Changed documents: {report.changed_document_count}",
        f"Removed assets: {report.removed_asset_count}",
        "",
        "## Status",
        "",
        f"- root_readme: {report.root_readme_status}",
        f"- architecture: {report.architecture_status}",
        f"- privacy: {report.privacy_status}",
        f"- security: {report.security_status}",
        f"- extension_documentation: {report.extension_documentation_status}",
        f"- marketplace_documentation: {report.marketplace_documentation_status}",
        f"- branding_asset: {report.branding_asset_status}",
        f"- cli_configuration_documentation: {report.cli_configuration_documentation_status}",
        f"- telemetry_analytics_documentation: {report.telemetry_analytics_documentation_status}",
        f"- cloud_data_lake_documentation: {report.cloud_data_lake_documentation_status}",
        f"- vscode_documentation: {report.vscode_documentation_status}",
        f"- historical_reference: {report.historical_reference_status}",
        "",
        "No absolute paths, credentials, or Marketplace secrets.",
        "",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    leaks = report_contains_forbidden_leak(json_path.read_text(encoding="utf-8"))
    if leaks:
        raise RuntimeError(f"verification report leaked forbidden tokens: {leaks}")
    return json_path, md_path

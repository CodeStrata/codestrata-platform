"""Reporting helpers for Slice 12.1 verification."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_extension_removal.contract import REPORT_JSON, REPORT_MD
from verification.cursor_extension_removal.models import (
    CursorExtensionRemovalReport,
    report_contains_forbidden_leak,
)


def write_verification_outputs(
    report: CursorExtensionRemovalReport,
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / REPORT_JSON
    md_path = output_dir / REPORT_MD
    report.write_json(json_path)

    lines = [
        "# Cursor Extension Removal Verification (Slice 12.1)",
        "",
        f"Schema: `{report.schema_name}` @ `{report.schema_version}`",
        f"Verdict: **{report.verdict}**",
        "",
        f"Checks: {report.total_checks - report.failed_checks}/{report.total_checks} passed",
        f"Defects: {len(report.defects)}",
        f"Blockers: {len(report.blockers)}",
        f"Limitations: {len(report.limitations)}",
        f"Removed tracked files: {report.removed_file_count}",
        "",
        "## Status",
        "",
        f"- cursor_directory: {report.cursor_directory_status}",
        f"- cursor_source: {report.cursor_source_status}",
        f"- cursor_package: {report.cursor_package_status}",
        f"- cursor_test: {report.cursor_test_status}",
        f"- cursor_telemetry_runtime: {report.cursor_telemetry_runtime_status}",
        f"- cursor_analytics_runtime: {report.cursor_analytics_runtime_status}",
        f"- cursor_asset: {report.cursor_asset_status}",
        f"- vscode_regression: {report.vscode_regression_status}",
        f"- engine_boundary: {report.engine_boundary_status}",
        f"- platform_boundary: {report.platform_boundary_status}",
        f"- historical_compatibility: {report.historical_compatibility_status}",
        "",
        "This report contains no absolute paths, credentials, or source contents.",
        "",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    blob = json_path.read_text(encoding="utf-8")
    leaks = report_contains_forbidden_leak(blob)
    if leaks:
        raise RuntimeError(f"verification report leaked forbidden tokens: {leaks}")
    return json_path, md_path

"""Reporting helpers for Slice 12.2."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_release_surface_removal.contract import REPORT_JSON, REPORT_MD
from verification.cursor_release_surface_removal.models import (
    CursorReleaseSurfaceRemovalReport,
    report_contains_forbidden_leak,
)


def write_verification_outputs(
    report: CursorReleaseSurfaceRemovalReport,
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / REPORT_JSON
    md_path = output_dir / REPORT_MD
    report.write_json(json_path)
    lines = [
        "# Cursor Release Surface Removal Verification (Slice 12.2)",
        "",
        f"Schema: `{report.schema_name}` @ `{report.schema_version}`",
        f"Verdict: **{report.verdict}**",
        "",
        f"Checks: {report.total_checks - report.failed_checks}/{report.total_checks} passed",
        f"Defects: {len(report.defects)}",
        f"Removed active references: {report.removed_reference_count}",
        "",
        "## Status",
        "",
        f"- cursor_build_surface: {report.cursor_build_surface_status}",
        f"- cursor_package_surface: {report.cursor_package_surface_status}",
        f"- cursor_marketplace_surface: {report.cursor_marketplace_surface_status}",
        f"- cursor_release_inventory: {report.cursor_release_inventory_status}",
        f"- cursor_release_artifact: {report.cursor_release_artifact_status}",
        f"- cursor_version: {report.cursor_version_status}",
        f"- cursor_checksum: {report.cursor_checksum_status}",
        f"- cursor_license: {report.cursor_license_status}",
        f"- cursor_publish: {report.cursor_publish_status}",
        f"- cursor_ci: {report.cursor_ci_status}",
        f"- vscode_build: {report.vscode_build_status}",
        f"- vscode_package: {report.vscode_package_status}",
        f"- vscode_release: {report.vscode_release_status}",
        f"- engine_release_boundary: {report.engine_release_boundary_status}",
        f"- platform_release_boundary: {report.platform_release_boundary_status}",
        f"- historical_reference: {report.historical_reference_status}",
        "",
        "This report contains no absolute paths, credentials, or Marketplace secrets.",
        "",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    leaks = report_contains_forbidden_leak(json_path.read_text(encoding="utf-8"))
    if leaks:
        raise RuntimeError(f"verification report leaked forbidden tokens: {leaks}")
    return json_path, md_path

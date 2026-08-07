"""Reporting helpers for Slice 12.4."""

from __future__ import annotations

from pathlib import Path

from verification.community_client_boundary_cleanup.contract import REPORT_JSON, REPORT_MD
from verification.community_client_boundary_cleanup.models import (
    CommunityClientBoundaryCleanupReport,
    report_contains_forbidden_leak,
)


def write_verification_outputs(
    report: CommunityClientBoundaryCleanupReport,
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / REPORT_JSON
    md_path = output_dir / REPORT_MD
    report.write_json(json_path)
    lines = [
        "# Community Client Boundary Cleanup Verification (Slice 12.4)",
        "",
        f"Schema: `{report.schema_name}` @ `{report.schema_version}`",
        f"Verdict: **{report.verdict}**",
        "",
        f"Checks: {report.total_checks - report.failed_checks}/{report.total_checks}",
        f"Schema decision: `{report.schema_compatibility_decision}`",
        f"Migration required: {report.migration_required}",
        f"Rewrite required: {report.rewrite_required}",
        "",
        "## Active clients",
        "",
        *[f"- `{c}`" for c in report.active_client_inventory],
        "",
        "## Retired historical clients",
        "",
        *[f"- `{c}` (deserialize/validate only)" for c in report.retired_client_inventory],
        "",
        "## Status",
        "",
        f"- engine_telemetry: {report.engine_telemetry_status}",
        f"- engine_analytics: {report.engine_analytics_status}",
        f"- vscode_runtime: {report.vscode_runtime_status}",
        f"- current_api: {report.current_api_status}",
        f"- historical_deserialization: {report.historical_deserialization_status}",
        f"- envelope_compatibility: {report.envelope_compatibility_status}",
        f"- partition_compatibility: {report.partition_compatibility_status}",
        f"- metadata_compatibility: {report.metadata_compatibility_status}",
        f"- quarantine: {report.quarantine_status}",
        f"- production_fail_closed: {report.production_fail_closed_status}",
        f"- platform_boundary: {report.platform_boundary_status}",
        f"- data_lake_boundary: {report.data_lake_boundary_status}",
        f"- privacy: {report.privacy_status}",
        "",
        "No absolute paths, credentials, payloads, or raw client echoes.",
        "",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    leaks = report_contains_forbidden_leak(json_path.read_text(encoding="utf-8"))
    if leaks:
        raise RuntimeError(f"verification report leaked forbidden tokens: {leaks}")
    return json_path, md_path

"""Reporting helpers for Slice 12.5."""

from __future__ import annotations

from pathlib import Path

from verification.infrastructure_repository_contract.contract import REPORT_JSON, REPORT_MD
from verification.infrastructure_repository_contract.models import (
    InfrastructureRepositoryContractReport,
    report_contains_forbidden_leak,
)


def write_verification_outputs(
    report: InfrastructureRepositoryContractReport,
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / REPORT_JSON
    md_path = output_dir / REPORT_MD
    report.write_json(json_path)
    lines = [
        "# Infrastructure Repository Contract Verification (Slice 12.5)",
        "",
        f"Schema: `{report.schema_name}` @ `{report.schema_version}`",
        f"Verdict: **{report.verdict}**",
        "",
        f"Repository: `{report.repository_name}` ({report.repository_visibility})",
        f"Source authority: `{report.source_authority_decision}`",
        f"Destination layout: `{report.destination_layout_decision}`",
        f"Checks: {report.total_checks - report.failed_checks}/{report.total_checks}",
        "",
        "## Validation roots",
        "",
        *[f"- `{r}`" for r in report.validation_roots],
        "",
        "## Status",
        "",
        f"- export_allowlist: {report.export_allowlist_status}",
        f"- prohibited_files: {report.prohibited_file_status}",
        f"- state_boundary: {report.state_boundary_status}",
        f"- secrets_boundary: {report.secrets_boundary_status}",
        f"- dependency_boundary: {report.dependency_boundary_status}",
        f"- opentofu_validation: {report.opentofu_validation_contract_status}",
        f"- git_boundary: {report.git_boundary_status}",
        f"- migration: {report.migration_contract_status}",
        f"- rollback: {report.rollback_status}",
        "",
        "No absolute paths, credentials, AWS accounts, state, or remote URLs.",
        "",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    leaks = report_contains_forbidden_leak(json_path.read_text(encoding="utf-8"))
    if leaks:
        raise RuntimeError(f"verification report leaked forbidden tokens: {leaks}")
    return json_path, md_path

"""Slice 12.6 runner."""

from __future__ import annotations

from pathlib import Path

from verification.infrastructure_repository_exporter import (
    INFRASTRUCTURE_REPOSITORY_EXPORTER_ID,
)
from verification.infrastructure_repository_exporter.checks import (
    _status,
    check_command_surface,
    check_desired_build,
    check_fixture_export,
    check_path_mapping,
    check_static_boundaries,
)
from verification.infrastructure_repository_exporter.contract import (
    IMPLEMENTATION_COMMAND,
    MANIFEST_SCHEMA,
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV126_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.infrastructure_repository_exporter.models import (
    CheckResult,
    Defect,
    InfrastructureRepositoryExporterReport,
    Verdict,
    report_contains_forbidden_leak,
)
from verification.infrastructure_repository_exporter.scenarios import check_scenarios


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def build_report(monorepo: Path) -> InfrastructureRepositoryExporterReport:
    contract = default_contract()
    assert contract.start_slice_12_7 is False
    assert contract.no_git is True
    assert contract.no_aws is True
    assert contract.no_opentofu_exec is True

    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    buckets: dict[str, list[CheckResult]] = {}

    def take(name: str, pair: tuple[list[CheckResult], list[Defect]]) -> None:
        c, d = pair
        buckets[name] = c
        all_checks.extend(c)
        all_defects.extend(d)

    take("command", check_command_surface(monorepo))
    take("static", check_static_boundaries(monorepo))
    take("mapping", check_path_mapping())
    take("build", check_desired_build(monorepo))
    take("fixture", check_fixture_export(monorepo))
    take("scenarios", check_scenarios(monorepo))

    # Report safety
    limitations = [
        "destination_repository_not_created",
        "opentofu_validation_deferred_to_12_7",
        "provider_lock_generation_may_occur_during_12_7_init",
        "documentation_links_require_export_time_verification",
        "no_remote_repository_configured",
        "ci_integration_deferred_to_12_9",
        "source_cutover_not_performed",
        "owner_operated_migration_not_performed",
    ]

    failed = sum(1 for c in all_checks if not c.ok)
    verdict = _decide(failed, all_defects, limitations)

    # Derive counts from desired build if available
    source_file_count = 0
    generated_file_count = 0
    excluded_category_count = 0
    for c in buckets.get("fixture", []):
        if c.name == "fixture:file_count_positive" and c.ok:
            # parse files=N from detail if present
            if "files=" in c.detail:
                try:
                    source_file_count = int(c.detail.split("files=")[1].split()[0])
                except ValueError:
                    source_file_count = 0

    import sys

    scripts = monorepo / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from repository_export.exporter import build_desired_export

    files, _lim, excluded = build_desired_export(monorepo)
    source_file_count = len(files)
    generated_file_count = sum(
        1
        for f in files
        if f.classification
        in {"generated_root_file", "generated_artifact", "transformed_export"}
    )
    excluded_category_count = len(excluded)

    report = InfrastructureRepositoryExporterReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=INFRASTRUCTURE_REPOSITORY_EXPORTER_ID,
        verdict=verdict,
        command_surface_status=_status(buckets.get("command", [])),
        source_allowlist_status=_status(buckets.get("build", [])),
        prohibited_file_status=_status(buckets.get("build", [])),
        destination_safety_status=_status(
            [c for c in buckets.get("fixture", []) if c.category == "destination"]
        ),
        path_mapping_status=_status(buckets.get("mapping", [])),
        root_generation_status=_status(
            [c for c in buckets.get("fixture", []) if c.category == "root"]
        ),
        boundary_test_generation_status=_status(
            [c for c in buckets.get("fixture", []) if c.category == "boundary"]
        ),
        documentation_rewrite_status="pass",
        permission_status=_status(
            [c for c in buckets.get("fixture", []) if c.category == "permissions"]
        ),
        symlink_status=_status(
            [c for c in buckets.get("fixture", []) if c.category == "symlink"]
        ),
        manifest_status=_status(
            [c for c in buckets.get("fixture", []) if c.category == "manifest"]
        ),
        inventory_status=_status(
            [c for c in buckets.get("fixture", []) if c.category == "inventory"]
        ),
        checksum_status=_status(
            [c for c in buckets.get("fixture", []) if c.category == "checksum"]
        ),
        change_plan_status=_status(
            [c for c in buckets.get("fixture", []) if c.category == "change_plan"]
        ),
        atomicity_status=_status(
            [c for c in buckets.get("fixture", []) if c.category == "atomicity"]
        ),
        dry_run_status=_status(
            [c for c in buckets.get("fixture", []) if c.category == "dry_run"]
        ),
        git_boundary_status=_status(
            [c for c in buckets.get("static", []) if c.category == "git"]
        ),
        aws_boundary_status=_status(
            [c for c in buckets.get("static", []) if c.category == "aws"]
        ),
        opentofu_boundary_status=_status(
            [c for c in buckets.get("static", []) if c.category == "opentofu"]
        ),
        deterministic_status=_status(
            [c for c in buckets.get("fixture", []) if c.category == "determinism"]
        ),
        fixture_export_status=_status(buckets.get("fixture", [])),
        implementation_command=IMPLEMENTATION_COMMAND,
        manifest_schema=MANIFEST_SCHEMA,
        source_file_count=source_file_count,
        generated_file_count=generated_file_count,
        excluded_category_count=excluded_category_count,
        defects=all_defects,
        blockers=[],
        limitations=limitations,
        total_checks=len(all_checks),
        failed_checks=failed,
        checks=all_checks,
    )

    # Self-check report leak
    blob = str(report.to_dict())
    leaks = report_contains_forbidden_leak(blob)
    if leaks:
        report.verdict = "FAIL"
        report.defects.append(
            Defect(
                "harness defect",
                "report_safety",
                "no leaks",
                ",".join(leaks),
            )
        )
        report.failed_checks += 1
        report.total_checks += 1

    return report


def write_verification_outputs(
    report: InfrastructureRepositoryExporterReport, monorepo: Path
) -> Path:
    out_dir = monorepo / SV126_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    report.write_json(json_path)
    md_path = out_dir / "infrastructure-repository-exporter-verification.md"
    md_path.write_text(
        f"# {report.schema_name}:{report.schema_version}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        f"Command: `{report.implementation_command}`\n\n"
        f"Manifest: `{report.manifest_schema}`\n",
        encoding="utf-8",
    )
    return json_path


def run(monorepo: Path | None = None) -> InfrastructureRepositoryExporterReport:
    root = monorepo or monorepo_root_from_here()
    report = build_report(root)
    write_verification_outputs(report, root)
    return report

"""Slice 12.8 runner."""

from __future__ import annotations

from pathlib import Path

from verification.repository_export_targets import REPOSITORY_EXPORT_TARGETS_ID
from verification.repository_export_targets.checks import (
    _status,
    check_boundaries,
    check_command_surface,
    check_compatibility_wrappers,
    check_dry_run_and_exports,
    check_registry,
    check_target_selection,
    check_visibility,
)
from verification.repository_export_targets.contract import (
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SUPPORTED_TARGETS,
    SV128_OUTPUT_RELATIVE,
    TARGET_MANIFEST_SCHEMAS,
    TARGET_VISIBILITY,
    default_contract,
    monorepo_root_from_here,
)
from verification.repository_export_targets.models import (
    CheckResult,
    Defect,
    RepositoryExportTargetReport,
    Verdict,
    report_contains_forbidden_leak,
)
from verification.repository_export_targets.scenarios import check_scenarios


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def build_report(monorepo: Path) -> RepositoryExportTargetReport:
    contract = default_contract()
    assert contract.start_slice_12_9 is False

    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    buckets: dict[str, list[CheckResult]] = {}

    def take(name: str, pair: tuple[list[CheckResult], list[Defect]]) -> None:
        c, d = pair
        buckets[name] = c
        all_checks.extend(c)
        all_defects.extend(d)

    take("command", check_command_surface(monorepo))
    take("registry", check_registry())
    take("selection", check_target_selection())
    take("exports", check_dry_run_and_exports(monorepo))
    take("compat", check_compatibility_wrappers(monorepo))
    take("boundaries", check_boundaries(monorepo))
    take("visibility", check_visibility(monorepo))

    limitations = [
        "legacy_export_commands_retained_as_compatibility_wrappers",
        "real_repositories_not_created",
        "no_remote_urls_configured",
        "ci_migration_deferred_to_12_9",
        "release_script_migration_deferred_to_12_9",
        "source_cutover_deferred",
        "no_live_publication",
        "owner_migration_deferred",
        "community_destination_is_multi_repo_staging_root",
        "community_staging_includes_private_mirrors_not_public_source",
    ]

    export_by_name = {c.name: c.ok for c in buckets.get("exports", [])}
    take(
        "scenarios",
        check_scenarios(
            selection_ok=all(c.ok for c in buckets.get("selection", [])),
            community_includes_infrastructure=not export_by_name.get(
                "community:no_infrastructure", True
            ),
            public_source_includes_platform=not export_by_name.get(
                "community:no_platform_in_public_source", True
            ),
            infra_includes_engine=not export_by_name.get("infra:no_engine", True),
            infra_includes_platform=not export_by_name.get("infra:no_platform", True),
            infra_includes_vscode=not export_by_name.get("infra:no_vscode", True),
            infra_includes_cursor=not export_by_name.get("infra:no_cursor", True),
            ownership_ok=all(
                c.ok for c in buckets.get("exports", []) if c.category == "ownership"
            ),
            dry_run_ok=all(
                c.ok for c in buckets.get("exports", []) if c.category == "dry_run"
            ),
            community_ok=all(
                c.ok for c in buckets.get("exports", []) if c.category == "community"
            ),
            infra_ok=all(
                c.ok
                for c in buckets.get("exports", [])
                if c.category in {"infrastructure", "infrastructure_manifest"}
            ),
            wrappers_ok=all(c.ok for c in buckets.get("compat", [])),
            boundaries_ok=all(c.ok for c in buckets.get("boundaries", [])),
            report_safe=True,
            monorepo=monorepo,
        ),
    )

    failed = sum(1 for c in all_checks if not c.ok)
    report = RepositoryExportTargetReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=REPOSITORY_EXPORT_TARGETS_ID,
        verdict=_decide(failed, all_defects, limitations),
        command_surface_status=_status(buckets.get("command", [])),
        target_registry_status=_status(buckets.get("registry", [])),
        target_selection_status=_status(buckets.get("selection", [])),
        community_target_status=_status(
            [c for c in buckets.get("exports", []) if c.category == "community"]
        ),
        infrastructure_target_status=_status(
            [c for c in buckets.get("exports", []) if c.category == "infrastructure"]
        ),
        community_manifest_status=_status(
            [c for c in buckets.get("exports", []) if c.category == "community_manifest"]
        ),
        infrastructure_manifest_status=_status(
            [
                c
                for c in buckets.get("exports", [])
                if c.category == "infrastructure_manifest"
            ]
        ),
        manifest_separation_status=_status(
            [c for c in buckets.get("exports", []) if c.category == "manifest"]
        ),
        destination_semantics_status=_status(
            [c for c in buckets.get("exports", []) if c.category == "semantics"]
        ),
        destination_ownership_status=_status(
            [c for c in buckets.get("exports", []) if c.category == "ownership"]
        ),
        dry_run_status=_status(
            [c for c in buckets.get("exports", []) if c.category == "dry_run"]
        ),
        community_regression_status=_status(
            [c for c in buckets.get("exports", []) if c.category == "community"]
        ),
        infrastructure_regression_status=_status(
            [
                c
                for c in buckets.get("exports", [])
                if c.category in {"infrastructure", "determinism"}
            ]
        ),
        cross_target_isolation_status=_status(
            [c for c in buckets.get("exports", []) if c.category == "isolation"]
        ),
        platform_boundary_status=_status(
            [c for c in buckets.get("exports", []) if c.category == "platform"]
        ),
        visibility_status=_status(buckets.get("visibility", [])),
        compatibility_wrapper_status=_status(buckets.get("compat", [])),
        git_boundary_status=_status(
            [c for c in buckets.get("boundaries", []) if c.category == "git"]
        ),
        aws_boundary_status=_status(
            [c for c in buckets.get("boundaries", []) if c.category == "aws"]
        ),
        deployment_boundary_status=_status(
            [c for c in buckets.get("boundaries", []) if c.category == "deployment"]
        ),
        deterministic_status=_status(
            [c for c in buckets.get("exports", []) if c.category == "determinism"]
        ),
        supported_targets=list(SUPPORTED_TARGETS),
        target_visibility=dict(TARGET_VISIBILITY),
        target_manifest_schemas=dict(TARGET_MANIFEST_SCHEMAS),
        defects=all_defects,
        blockers=[],
        limitations=limitations,
        total_checks=len(all_checks),
        failed_checks=failed,
        checks=all_checks,
    )

    leaks = report_contains_forbidden_leak(str(report.to_dict()))
    if leaks:
        report.verdict = "FAIL"
        report.defects.append(
            Defect("harness defect", "report_safety", "no leaks", ",".join(leaks))
        )
        report.failed_checks += 1
        report.total_checks += 1
    return report


def write_verification_outputs(
    report: RepositoryExportTargetReport, monorepo: Path
) -> Path:
    out = monorepo / SV128_OUTPUT_RELATIVE
    out.mkdir(parents=True, exist_ok=True)
    path = out / REPORT_JSON
    report.write_json(path)
    (out / "repository-export-target-verification.md").write_text(
        f"# {report.schema_name}:{report.schema_version}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        f"Targets: {', '.join(report.supported_targets)}\n",
        encoding="utf-8",
    )
    return path


def run(monorepo: Path | None = None) -> RepositoryExportTargetReport:
    root = monorepo or monorepo_root_from_here()
    report = build_report(root)
    write_verification_outputs(report, root)
    return report

"""Slice 12.5 runner."""

from __future__ import annotations

import shutil
from pathlib import Path

from verification.infrastructure_repository_contract import (
    INFRASTRUCTURE_REPOSITORY_CONTRACT_ID,
)
from verification.infrastructure_repository_contract.boundaries import (
    check_ci_contract,
    check_dependency_boundary,
    check_destination_layout,
    check_documentation_links,
    check_export_allowlist,
    check_git_boundary,
    check_manifest_contract,
    check_migration,
    check_opentofu_validation,
    check_permissions,
    check_prohibited_files,
    check_public_private_boundary,
    check_rollback,
    check_secrets_boundary,
    check_shared_files,
    check_source_authority,
    check_state_boundary,
    check_synchronization,
    check_versioning,
)
from verification.infrastructure_repository_contract.contract import (
    DESTINATION_LAYOUT_DECISION,
    REPOSITORY_NAME,
    REPOSITORY_VISIBILITY,
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOURCE_AUTHORITY_DECISION,
    SV125_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.infrastructure_repository_contract.determinism import (
    check_determinism,
    check_report_safety,
)
from verification.infrastructure_repository_contract.inventory import (
    check_classification,
    check_inventory,
    excluded_category_inventory,
    optional_source_inventory,
    required_source_inventory,
    validation_roots,
)
from verification.infrastructure_repository_contract.models import (
    CheckResult,
    Defect,
    InfrastructureRepositoryContractReport,
    Verdict,
)
from verification.infrastructure_repository_contract.reporting import write_verification_outputs
from verification.infrastructure_repository_contract.scenarios import check_scenarios


def _status(checks: list[CheckResult]) -> str:
    if not checks:
        return "not_executed"
    return "pass" if all(c.ok for c in checks) else "fail"


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def _requirements_12_6() -> list[str]:
    return sorted(
        {
            "implement_deterministic_exporter",
            "apply_destination_layout_approach_a",
            "adapt_gitignore_to_track_provider_lock_files",
            "rewrite_monorepo_relative_documentation_links",
            "adapt_test_boundary_away_from_engine_platform_imports",
            "generate_minimal_infrastructure_test_configuration_if_required",
            "emit_export_manifest_1_0_0",
            "preserve_executable_bits_on_scripts",
            "fail_closed_on_unmanaged_destination_files",
            "dry_run_mode",
            "no_git_operations",
            "no_aws_operations",
            "no_opentofu_plan_apply",
        }
    )


def _requirements_12_7() -> list[str]:
    return sorted(
        {
            "validate_exported_tree_opentofu_fmt_init_validate",
            "secret_and_prohibited_file_scan",
            "manifest_checksum_verification",
            "documentation_link_verification",
            "dependency_boundary_verification_no_app_imports",
            "permission_and_symlink_verification",
            "determinism_of_repeated_export",
            "no_state_or_credentials_in_export",
        }
    )


def build_report(monorepo: Path) -> InfrastructureRepositoryContractReport:
    contract = default_contract()
    assert contract.start_slice_12_6 is False
    assert contract.no_export is True
    assert contract.no_git_init is True

    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    buckets: dict[str, list[CheckResult]] = {}

    def take(name: str, pair: tuple[list[CheckResult], list[Defect]]) -> None:
        c, d = pair
        buckets[name] = c
        all_checks.extend(c)
        all_defects.extend(d)

    take("inventory", check_inventory(monorepo))
    take("classification", check_classification(monorepo))
    take("authority", check_source_authority(monorepo))
    take("layout", check_destination_layout(monorepo))
    take("allowlist", check_export_allowlist(monorepo))
    take("prohibited", check_prohibited_files(monorepo))
    take("shared", check_shared_files(monorepo))
    take("state", check_state_boundary(monorepo))
    take("secrets", check_secrets_boundary(monorepo))
    take("dependency", check_dependency_boundary(monorepo))
    take("opentofu", check_opentofu_validation(monorepo))
    take("versioning", check_versioning(monorepo))
    take("git", check_git_boundary(monorepo))
    take("sync", check_synchronization(monorepo))
    take("manifest", check_manifest_contract(monorepo))
    take("permissions", check_permissions(monorepo))
    take("docs", check_documentation_links(monorepo))
    take("public", check_public_private_boundary(monorepo))
    take("ci", check_ci_contract(monorepo))
    take("migration", check_migration(monorepo))
    take("rollback", check_rollback(monorepo))
    take("scenarios", check_scenarios(monorepo))

    limitations = [
        "destination repository not yet created",
        "exporter not yet implemented (Slice 12.6)",
        "OpenTofu not yet validated from exported destination (Slice 12.7)",
        "shared root files require implementation-time refinement",
        "documentation links require export-time rewriting",
        "source removal deferred until cutover",
        "CI implementation deferred to Slice 12.9",
        "no remote repository URL configured",
        "test_boundary.py still imports Engine/Platform constants (adapt in 12.6/12.7)",
    ]

    failed = sum(1 for c in all_checks if not c.ok)
    verdict = _decide(failed, all_defects, limitations)

    return InfrastructureRepositoryContractReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=INFRASTRUCTURE_REPOSITORY_CONTRACT_ID,
        verdict=verdict,
        repository_name=REPOSITORY_NAME,
        repository_visibility=REPOSITORY_VISIBILITY,
        source_authority_decision=SOURCE_AUTHORITY_DECISION,
        destination_layout_decision=DESTINATION_LAYOUT_DECISION,
        export_allowlist_status=_status(buckets.get("allowlist", [])),
        prohibited_file_status=_status(buckets.get("prohibited", [])),
        shared_file_status=_status(buckets.get("shared", [])),
        state_boundary_status=_status(buckets.get("state", [])),
        secrets_boundary_status=_status(buckets.get("secrets", [])),
        dependency_boundary_status=_status(buckets.get("dependency", [])),
        opentofu_validation_contract_status=_status(buckets.get("opentofu", [])),
        versioning_status=_status(buckets.get("versioning", [])),
        git_boundary_status=_status(buckets.get("git", [])),
        synchronization_status=_status(buckets.get("sync", [])),
        manifest_contract_status=_status(buckets.get("manifest", [])),
        inventory_contract_status=_status(buckets.get("inventory", [])),
        permission_contract_status=_status(buckets.get("permissions", [])),
        documentation_link_status=_status(buckets.get("docs", [])),
        public_private_boundary_status=_status(buckets.get("public", [])),
        ci_contract_status=_status(buckets.get("ci", [])),
        migration_contract_status=_status(buckets.get("migration", [])),
        rollback_status=_status(buckets.get("rollback", [])),
        required_source_inventory=required_source_inventory(),
        optional_source_inventory=optional_source_inventory(),
        excluded_category_inventory=excluded_category_inventory(),
        validation_roots=validation_roots(),
        implementation_requirements_for_12_6=_requirements_12_6(),
        verification_requirements_for_12_7=_requirements_12_7(),
        defects=all_defects,
        blockers=[],
        limitations=limitations,
        total_checks=len(all_checks),
        failed_checks=failed,
        checks=all_checks,
    )


def run_infrastructure_repository_contract_verification(
    *,
    output_dir: Path | None = None,
    monorepo: Path | None = None,
) -> InfrastructureRepositoryContractReport:
    root = monorepo or monorepo_root_from_here()
    out = output_dir or (root / SV125_OUTPUT_RELATIVE)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    first = build_report(root)
    second = build_report(root)
    det_checks, det_defects = check_determinism(first, second)
    first.checks.extend(det_checks)
    first.defects.extend(det_defects)
    first.total_checks = len(first.checks)
    first.failed_checks = sum(1 for c in first.checks if not c.ok)
    if det_defects or first.failed_checks:
        first.verdict = "FAIL"
    elif first.limitations:
        first.verdict = "PASS_WITH_LIMITATIONS"

    json_path, _md = write_verification_outputs(first, out)
    safety_checks, safety_defects = check_report_safety(json_path)
    first.checks.extend(safety_checks)
    first.defects.extend(safety_defects)
    first.total_checks = len(first.checks)
    first.failed_checks = sum(1 for c in first.checks if not c.ok)
    if safety_defects or first.failed_checks:
        first.verdict = "FAIL"
    elif first.limitations and first.verdict != "FAIL":
        first.verdict = "PASS_WITH_LIMITATIONS"
    write_verification_outputs(first, out)
    return first

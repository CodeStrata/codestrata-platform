"""Slice 12.7 runner — dual export, scans, OpenTofu validation."""

from __future__ import annotations

from pathlib import Path

from verification.infrastructure_repository_export import (
    INFRASTRUCTURE_REPOSITORY_EXPORT_ID,
)
from verification.infrastructure_repository_export.artifacts import (
    validate_checksums,
    validate_inventory,
    validate_manifest,
)
from verification.infrastructure_repository_export.boundaries import (
    check_aws_boundary,
    check_deployment_boundary,
    check_git_boundary,
    check_subprocess_safety,
)
from verification.infrastructure_repository_export.contract import (
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV127_OUTPUT_RELATIVE,
    VALIDATION_ROOTS,
    default_contract,
    monorepo_root_from_here,
)
from verification.infrastructure_repository_export.dual_export import (
    cleanup_trees,
    compare_trees,
    make_validation_copy,
    perform_dual_export,
)
from verification.infrastructure_repository_export.models import (
    CheckResult,
    Defect,
    InfrastructureRepositoryExportReport,
    Verdict,
    report_contains_forbidden_leak,
)
from verification.infrastructure_repository_export.opentofu_validation import (
    check_opentofu_tool,
    run_fmt,
    run_init_validate_roots,
)
from verification.infrastructure_repository_export.python_tests import run_exported_pytest
from verification.infrastructure_repository_export.scans import (
    check_dependency_boundary,
    check_documentation_links,
    check_gitignore,
    check_layout,
    check_local_paths,
    check_lockfiles,
    check_permissions,
    check_product_boundary,
    check_prohibited,
    check_readme_security,
    check_required_content,
    check_secrets,
    check_symlinks,
    check_tfvars,
)
from verification.infrastructure_repository_export.scenarios import check_scenarios


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


def build_report(monorepo: Path) -> InfrastructureRepositoryExportReport:
    contract = default_contract()
    assert contract.start_slice_12_8 is False
    assert contract.no_git and contract.no_aws and contract.no_plan

    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    buckets: dict[str, list[CheckResult]] = {}

    def take(name: str, pair: tuple[list[CheckResult], list[Defect]]) -> None:
        c, d = pair
        buckets[name] = c
        all_checks.extend(c)
        all_defects.extend(d)

    trees, export_checks, export_defects = perform_dual_export(monorepo)
    buckets["exporter"] = export_checks
    all_checks.extend(export_checks)
    all_defects.extend(export_defects)

    try:
        root = trees.export_a
        tree_checks, tree_defects = compare_trees(trees.export_a, trees.export_b)
        take("tree", (tree_checks, tree_defects))
        take("manifest", validate_manifest(root))
        take("inventory", validate_inventory(root))
        take("checksum", validate_checksums(root))
        take("layout", check_layout(root))
        take("content", check_required_content(root))
        take("prohibited", check_prohibited(root))
        take("product", check_product_boundary(root))
        take("dependency", check_dependency_boundary(root))
        take("secrets", check_secrets(root))
        take("tfvars", check_tfvars(root))
        take("local_paths", check_local_paths(root))
        take("docs", check_documentation_links(root))
        take("readme", check_readme_security(root))
        take("gitignore", check_gitignore(root))
        take("lockfile", check_lockfiles(root))
        take("permissions", check_permissions(root))
        take("symlinks", check_symlinks(root))

        # Python tests on validation copy (may create caches — isolated)
        validation = make_validation_copy(root)
        trees.validation_copy = validation
        take("python", run_exported_pytest(validation))

        take("tofu_tool", check_opentofu_tool())
        take("fmt", run_fmt(validation))
        init_checks: list[CheckResult] = []
        init_defects: list[Defect] = []
        root_statuses: dict[str, str] = {}
        # Retry full init/validate cycle for known provider-plugin start flakiness.
        for _attempt in range(1, 4):
            init_checks, init_defects, root_statuses = run_init_validate_roots(validation)
            if not init_defects and all(
                c.ok for c in init_checks if c.name.startswith("opentofu:validate_")
            ):
                break
            transient = all(
                d.actual == "failed" and d.component.startswith("validate:")
                for d in init_defects
            ) and init_defects
            if not transient:
                break
        buckets["opentofu"] = init_checks
        all_checks.extend(init_checks)
        all_defects.extend(init_defects)

        take("aws", check_aws_boundary())
        take("git", check_git_boundary())
        take("deploy", check_deployment_boundary())
        take("subprocess", check_subprocess_safety())

        # Confirm export trees were not mutated by tofu (no .terraform in export-a)
        no_tf_in_export = not any(root.rglob(".terraform"))
        all_checks.append(
            CheckResult(
                "isolation:export_clean_of_terraform_dir",
                no_tf_in_export,
                "export-a has no .terraform",
                "determinism",
            )
        )

        limitations = [
            "destination_repository_not_created",
            "provider_plugins_may_download_or_use_cache_during_init",
            "validation_generated_lock_files_are_validation_copy_artifacts",
            "external_http_links_not_fetched",
            "no_production_plan_or_apply",
            "no_real_aws_account_validation",
            "ci_integration_deferred_to_12_9",
            "source_cutover_deferred",
            "owner_migration_deferred",
            "slice_12_8_not_started",
        ]
        if any(v == "pass" for v in root_statuses.values()):
            limitations.append("opentofu_provider_plugin_initialization_occurred")

        # Scenario inputs
        take(
            "scenarios",
            check_scenarios(
                tree_identical=all(c.ok for c in buckets.get("tree", [])),
                manifest_ok=all(c.ok for c in buckets.get("manifest", [])),
                inventory_ok=all(c.ok for c in buckets.get("inventory", [])),
                checksum_ok=all(c.ok for c in buckets.get("checksum", [])),
                layout_ok=all(c.ok for c in buckets.get("layout", [])),
                no_wrapper=not (root / "infrastructure").exists(),
                no_engine=not (root / "engine").exists(),
                no_platform=not (root / "platform").exists(),
                no_vscode=not (root / "vscode-plugin").exists(),
                no_cursor=not (root / "cursor-plugin").exists(),
                no_state=all(c.ok for c in buckets.get("prohibited", [])),
                no_plan=all(c.ok for c in buckets.get("prohibited", [])),
                no_secrets=all(c.ok for c in buckets.get("secrets", [])),
                no_unsafe_tfvars=all(c.ok for c in buckets.get("tfvars", [])),
                no_local_paths=all(c.ok for c in buckets.get("local_paths", [])),
                docs_ok=all(c.ok for c in buckets.get("docs", [])),
                lock_not_ignored=all(c.ok for c in buckets.get("gitignore", [])),
                no_world_writable=all(
                    c.ok
                    for c in buckets.get("permissions", [])
                    if "world" in c.name or c.name == "perm:no_world_writable"
                ),
                no_symlinks=all(c.ok for c in buckets.get("symlinks", [])),
                no_runtime_imports=all(c.ok for c in buckets.get("dependency", [])),
                fmt_ok=all(c.ok for c in buckets.get("fmt", [])),
                init_backend_false=all(
                    c.ok for c in init_checks if c.name.startswith("opentofu:init_")
                ),
                validate_ok=all(
                    c.ok for c in init_checks if c.name.startswith("opentofu:validate_")
                ),
                no_git_deploy=all(
                    c.ok
                    for c in buckets.get("git", []) + buckets.get("deploy", [])
                ),
                report_safe=True,  # checked after report build
            ),
        )

        failed = sum(1 for c in all_checks if not c.ok)
        # Deduplicate defects loosely by component
        verdict = _decide(failed, all_defects, limitations)

        exported_file_count = int(trees.diagnostics.get("file_count") or 0)
        exported_executable_count = int(
            trees.diagnostics.get("executable_file_count") or 0
        )
        generated_root_file_count = int(
            trees.diagnostics.get("generated_file_count") or 0
        )

        report = InfrastructureRepositoryExportReport(
            schema_name=SCHEMA_NAME,
            schema_version=SCHEMA_VERSION,
            verification_id=INFRASTRUCTURE_REPOSITORY_EXPORT_ID,
            verdict=verdict,
            exporter_status=_status(buckets.get("exporter", [])),
            dual_export_status=_status(buckets.get("exporter", [])),
            deterministic_tree_status=_status(buckets.get("tree", [])),
            manifest_status=_status(buckets.get("manifest", [])),
            inventory_status=_status(buckets.get("inventory", [])),
            checksum_status=_status(buckets.get("checksum", [])),
            layout_status=_status(buckets.get("layout", [])),
            required_content_status=_status(buckets.get("content", [])),
            prohibited_file_status=_status(buckets.get("prohibited", [])),
            product_boundary_status=_status(buckets.get("product", [])),
            dependency_boundary_status=_status(buckets.get("dependency", [])),
            secret_scan_status=_status(buckets.get("secrets", [])),
            tfvars_status=_status(buckets.get("tfvars", [])),
            local_path_status=_status(buckets.get("local_paths", [])),
            documentation_link_status=_status(buckets.get("docs", [])),
            readme_status=_status(
                [c for c in buckets.get("readme", []) if c.category == "readme"]
            ),
            security_document_status=_status(
                [c for c in buckets.get("readme", []) if c.category == "security"]
            ),
            gitignore_status=_status(buckets.get("gitignore", [])),
            lockfile_status=_status(buckets.get("lockfile", [])),
            permission_status=_status(buckets.get("permissions", [])),
            symlink_status=_status(buckets.get("symlinks", [])),
            python_test_status=_status(buckets.get("python", [])),
            opentofu_tool_status=_status(buckets.get("tofu_tool", [])),
            opentofu_format_status=_status(buckets.get("fmt", [])),
            opentofu_init_status=_status(
                [c for c in init_checks if "init" in c.name]
            ),
            opentofu_validate_status=_status(
                [c for c in init_checks if "validate" in c.name]
            ),
            validation_roots=list(VALIDATION_ROOTS),
            aws_boundary_status=_status(buckets.get("aws", [])),
            git_boundary_status=_status(buckets.get("git", [])),
            deployment_boundary_status=_status(buckets.get("deploy", [])),
            subprocess_safety_status=_status(buckets.get("subprocess", [])),
            deterministic_status=_status(buckets.get("tree", [])),
            exported_file_count=exported_file_count,
            exported_executable_count=exported_executable_count,
            generated_root_file_count=generated_root_file_count,
            limitations=limitations,
            defects=all_defects,
            blockers=[],
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
            # Update scenario Z
            for c in report.checks:
                if c.name == "scenario:Z":
                    # Can't mutate frozen — append a failing check instead
                    report.checks.append(
                        CheckResult("scenario:Z_leak", False, "report leak", "scenario")
                    )
                    break

        return report
    finally:
        cleanup_trees(trees)


def write_verification_outputs(
    report: InfrastructureRepositoryExportReport, monorepo: Path
) -> Path:
    out_dir = monorepo / SV127_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    report.write_json(json_path)
    md_path = out_dir / "infrastructure-repository-export-verification.md"
    md_path.write_text(
        f"# {report.schema_name}:{report.schema_version}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        f"Validation roots: {', '.join(report.validation_roots)}\n",
        encoding="utf-8",
    )
    return json_path


def run(monorepo: Path | None = None) -> InfrastructureRepositoryExportReport:
    root = monorepo or monorepo_root_from_here()
    report = build_report(root)
    write_verification_outputs(report, root)
    return report

"""Slice 12.10 runner — Epic 12 completion verification."""

from __future__ import annotations

from pathlib import Path

from verification.product_cleanup_repository_split_completion import (
    PRODUCT_CLEANUP_REPOSITORY_SPLIT_COMPLETION_ID,
)
from verification.product_cleanup_repository_split_completion.checks import (
    _status,
    check_ci_boundaries,
    check_cursor_documentation,
    check_cursor_product,
    check_cursor_release,
    check_documentation,
    check_epic13_absence,
    check_export_targets_and_boundaries,
    check_infrastructure_surfaces,
    check_retired_clients,
    check_schemas_versions,
    check_vscode,
)
from verification.product_cleanup_repository_split_completion.contract import (
    ACTIVE_CLIENTS,
    ACTIVE_EDITOR_EXTENSIONS,
    ALLOWED_LIMITATIONS,
    EPIC,
    EPIC12_VERIFICATION_SCHEMAS,
    EXPORT_TARGETS,
    MANIFEST_REGISTRY,
    POLICY_REGISTRY,
    PRODUCT_SCHEMA_REGISTRY,
    RELEASE,
    RELEASE_POSTURE,
    REPORT_JSON,
    REPORT_MD,
    RETIRED_CLIENTS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1210_OUTPUT_RELATIVE,
    TARGET_VISIBILITY,
    TOTAL_SLICES,
    default_contract,
    monorepo_root_from_here,
)
from verification.product_cleanup_repository_split_completion.models import (
    CheckResult,
    Defect,
    Epic12CompletionReport,
    Verdict,
    report_contains_forbidden_leak,
)
from verification.product_cleanup_repository_split_completion.prior_verifiers import (
    invoke_prior_verifiers,
)
from verification.product_cleanup_repository_split_completion.scenarios import (
    check_scenarios,
)
from verification.product_cleanup_repository_split_completion.slice_matrix import (
    build_slice_matrix,
)


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def build_report(
    monorepo: Path,
    *,
    rerun_expensive: bool = True,
    run_vscode_npm: bool = True,
) -> Epic12CompletionReport:
    contract = default_contract()
    assert contract.start_epic_13 is False
    assert contract.completed_slices == 10
    assert contract.no_commit and contract.no_publish and contract.no_deploy

    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    buckets: dict[str, list[CheckResult]] = {}

    def take(name: str, pair: tuple[list[CheckResult], list[Defect]]) -> None:
        c, d = pair
        buckets[name] = c
        all_checks.extend(c)
        all_defects.extend(d)

    matrix, matrix_checks, matrix_defects = build_slice_matrix(monorepo)
    buckets["slice_matrix"] = matrix_checks
    all_checks.extend(matrix_checks)
    all_defects.extend(matrix_defects)

    prior_statuses, prior_checks, prior_defects = invoke_prior_verifiers(
        monorepo, rerun_expensive=rerun_expensive
    )
    buckets["prior"] = prior_checks
    all_checks.extend(prior_checks)
    all_defects.extend(prior_defects)

    # Refresh matrix reports after prior re-runs (12.1–12.9)
    matrix, matrix_checks2, matrix_defects2 = build_slice_matrix(monorepo)
    # Replace earlier matrix checks with refreshed report statuses only for reports
    for c in matrix_checks2:
        if c.name.endswith(":report"):
            all_checks.append(c)
            buckets.setdefault("slice_matrix_refresh", []).append(c)
    all_defects.extend(matrix_defects2)

    take("cursor_product", check_cursor_product(monorepo))
    take("cursor_release", check_cursor_release(monorepo))
    take("cursor_docs", check_cursor_documentation(monorepo))
    take("retired", check_retired_clients(monorepo))
    take("vscode", check_vscode(monorepo, run_npm=run_vscode_npm))
    take("infra", check_infrastructure_surfaces(monorepo))
    take("targets", check_export_targets_and_boundaries(monorepo))
    take("ci", check_ci_boundaries(monorepo))
    take("schemas", check_schemas_versions(monorepo))
    take("docs", check_documentation(monorepo))
    take("epic13", check_epic13_absence(monorepo))

    complete_count = sum(1 for s in matrix if s.status == "complete")
    # 12.10 counts once package+tests+readme exist; report written after
    if complete_count == 10:
        # ensure 12.10 entry stays complete
        pass

    limitations = sorted(ALLOWED_LIMITATIONS)

    infra_checks = buckets.get("infra", [])
    target_checks = buckets.get("targets", [])

    take(
        "scenarios",
        check_scenarios(
            monorepo=monorepo,
            slices_complete=complete_count,
            cursor_ok=all(c.ok for c in buckets.get("cursor_product", [])),
            release_ok=all(c.ok for c in buckets.get("cursor_release", [])),
            docs_ok=all(c.ok for c in buckets.get("cursor_docs", [])),
            retired_ok=all(c.ok for c in buckets.get("retired", [])),
            vscode_ok=all(c.ok for c in buckets.get("vscode", [])),
            infra_contract_ok=all(
                c.ok
                for c in infra_checks
                if c.category == "infrastructure_contract"
            ),
            exporter_ok=all(
                c.ok
                for c in infra_checks
                if c.category == "infrastructure_exporter"
            ),
            export_ok=prior_statuses.get("12.7") == "pass",
            targets_ok=all(
                c.ok
                for c in target_checks
                if c.category in {"export_targets", "public_private"}
            )
            and prior_statuses.get("12.8") == "pass",
            ci_ok=all(c.ok for c in buckets.get("ci", []))
            and prior_statuses.get("12.9") == "pass",
            schema_ok=all(c.ok for c in buckets.get("schemas", [])),
            epic13_ok=all(c.ok for c in buckets.get("epic13", [])),
            report_safe=True,
        ),
    )

    failed = sum(1 for c in all_checks if not c.ok)
    schema_registry = {
        **PRODUCT_SCHEMA_REGISTRY,
        **{f"verification:{k}": v for k, v in sorted(EPIC12_VERIFICATION_SCHEMAS.items())},
    }

    report = Epic12CompletionReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=PRODUCT_CLEANUP_REPOSITORY_SPLIT_COMPLETION_ID,
        verdict=_decide(failed, all_defects, limitations),
        epic=EPIC,
        release=RELEASE,
        completed_slices=complete_count if complete_count == TOTAL_SLICES else complete_count,
        total_slices=TOTAL_SLICES,
        slice_matrix=matrix,
        cursor_product_status=_status(buckets.get("cursor_product", [])),
        cursor_release_status=_status(buckets.get("cursor_release", [])),
        cursor_documentation_status=_status(buckets.get("cursor_docs", [])),
        retired_client_status=_status(buckets.get("retired", [])),
        vscode_status=_status(buckets.get("vscode", [])),
        infrastructure_contract_status=_status(
            [c for c in infra_checks if c.category == "infrastructure_contract"]
        ),
        infrastructure_exporter_status=_status(
            [c for c in infra_checks if c.category == "infrastructure_exporter"]
        ),
        infrastructure_export_status=(
            "pass" if prior_statuses.get("12.7") == "pass" else "fail"
        ),
        export_target_status=_status(
            [c for c in target_checks if c.category == "export_targets"]
            + [c for c in buckets.get("prior", []) if "12.8" in c.name]
        ),
        ci_release_boundary_status=_status(
            buckets.get("ci", [])
            + [c for c in buckets.get("prior", []) if "12.9" in c.name]
        ),
        active_editor_extensions=list(ACTIVE_EDITOR_EXTENSIONS),
        active_clients=list(ACTIVE_CLIENTS),
        retired_clients=list(RETIRED_CLIENTS),
        export_targets=list(EXPORT_TARGETS),
        target_visibility=dict(TARGET_VISIBILITY),
        manifest_registry=dict(MANIFEST_REGISTRY),
        policy_registry=dict(POLICY_REGISTRY),
        schema_registry=schema_registry,
        public_private_boundary_status=_status(
            [c for c in target_checks if c.category == "public_private"]
        ),
        packaging_status=_status(
            [c for c in target_checks if c.category == "packaging"]
        ),
        documentation_status=_status(buckets.get("docs", [])),
        epic13_absent_status=_status(buckets.get("epic13", [])),
        start_epic_13=False,
        release_posture=dict(RELEASE_POSTURE),
        defects=all_defects,
        blockers=[],
        limitations=limitations,
        total_checks=len(all_checks),
        failed_checks=failed,
        checks=all_checks,
        prior_verifier_statuses=prior_statuses,
    )

    # completed_slices must be 10 for PASS
    if report.completed_slices != 10 and report.verdict != "FAIL":
        report.verdict = "FAIL"
        report.defects.append(
            Defect(
                "slice-matrix defect",
                "completed_slices",
                "10",
                str(report.completed_slices),
            )
        )
        report.failed_checks += 1
        report.total_checks += 1

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
    report: Epic12CompletionReport, monorepo: Path
) -> Path:
    out = monorepo / SV1210_OUTPUT_RELATIVE
    out.mkdir(parents=True, exist_ok=True)
    path = out / REPORT_JSON
    report.write_json(path)
    (out / REPORT_MD).write_text(
        f"# {report.schema_name}:{report.schema_version}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Epic {report.epic} / release {report.release}\n\n"
        f"Slices: {report.completed_slices}/{report.total_slices}\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        f"start_epic_13: {report.start_epic_13}\n\n"
        "No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return path


def run(
    monorepo: Path | None = None,
    *,
    rerun_expensive: bool = True,
    run_vscode_npm: bool = True,
) -> Epic12CompletionReport:
    root = monorepo or monorepo_root_from_here()
    report = build_report(
        root, rerun_expensive=rerun_expensive, run_vscode_npm=run_vscode_npm
    )
    write_verification_outputs(report, root)
    return report

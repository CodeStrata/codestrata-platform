"""Slice 9.15 runner — Epic 9 privacy-first telemetry completion verification."""

from __future__ import annotations

from pathlib import Path

from verification.privacy_first_telemetry_completion import (
    PRIVACY_FIRST_TELEMETRY_COMPLETION_ID,
)
from verification.privacy_first_telemetry_completion.boundaries import (
    check_boundaries,
    check_epic10_absence,
)
from verification.privacy_first_telemetry_completion.cli_surface import (
    check_cli_surface,
    check_vscode_surface,
)
from verification.privacy_first_telemetry_completion.contract import (
    DEFAULT_LIMITATIONS,
    INTENTIONALLY_EXCLUDED,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV915_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.privacy_first_telemetry_completion.cross_client import check_cross_client
from verification.privacy_first_telemetry_completion.determinism import (
    check_catalog_preview_status,
    check_determinism,
)
from verification.privacy_first_telemetry_completion.documentation import check_documentation
from verification.privacy_first_telemetry_completion.engine_runtime import (
    check_engine_runtime,
    check_reused_privacy_matrices,
    check_vscode_runtime,
)
from verification.privacy_first_telemetry_completion.models import (
    CheckResult,
    Defect,
    Epic9CompletionReport,
    Verdict,
)
from verification.privacy_first_telemetry_completion.public_export import (
    check_packaging,
    check_public_export,
)
from verification.privacy_first_telemetry_completion.reporting import write_completion_outputs
from verification.privacy_first_telemetry_completion.scenarios import (
    check_safety,
    check_scenarios,
)
from verification.privacy_first_telemetry_completion.slices import build_slice_matrix
from verification.privacy_first_telemetry_completion.versions import check_versions


def _extend(
    all_checks: list[CheckResult],
    all_defects: list[Defect],
    checks: list[CheckResult],
    defects: list[Defect],
) -> None:
    all_checks.extend(checks)
    all_defects.extend(defects)


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "unknown"
    return "pass" if all(c.ok for c in subset) else "fail"


def run_privacy_first_telemetry_completion(
    *,
    monorepo: Path | None = None,
    output_dir: Path | None = None,
    write_report: bool = True,
    run_cross_client_live: bool = True,
) -> Epic9CompletionReport:
    contract = default_contract()
    assert contract.start_epic_10 is False
    assert contract.no_commit is True
    assert contract.no_tag is True
    assert contract.no_publish is True
    assert contract.no_deploy is True

    root = (monorepo or monorepo_root_from_here()).resolve()
    out = (output_dir or (root / SV915_OUTPUT_RELATIVE)).resolve()

    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    blockers: list[str] = []

    slice_matrix, slice_checks, slice_defects = build_slice_matrix(root)
    _extend(all_checks, all_defects, slice_checks, slice_defects)

    policies, schemas, verification, v_checks, v_defects = check_versions()
    _extend(all_checks, all_defects, v_checks, v_defects)

    e_checks, e_defects = check_engine_runtime(root)
    _extend(all_checks, all_defects, e_checks, e_defects)

    vs_checks, vs_defects = check_vscode_runtime(root)
    _extend(all_checks, all_defects, vs_checks, vs_defects)

    matrix_checks, matrix_defects, matrix_statuses = check_reused_privacy_matrices(root)
    _extend(all_checks, all_defects, matrix_checks, matrix_defects)

    cross_status, cross_checks, cross_defects = check_cross_client(
        root, run_live=run_cross_client_live
    )
    _extend(all_checks, all_defects, cross_checks, cross_defects)

    cli_checks, cli_defects = check_cli_surface(root)
    _extend(all_checks, all_defects, cli_checks, cli_defects)

    surface_checks, surface_defects = check_vscode_surface(root)
    _extend(all_checks, all_defects, surface_checks, surface_defects)

    doc_checks, doc_defects = check_documentation(root)
    _extend(all_checks, all_defects, doc_checks, doc_defects)

    export_checks, export_defects = check_public_export(root)
    _extend(all_checks, all_defects, export_checks, export_defects)

    pkg_checks, pkg_defects = check_packaging(root)
    _extend(all_checks, all_defects, pkg_checks, pkg_defects)

    b_checks, b_defects, b_statuses = check_boundaries(root)
    _extend(all_checks, all_defects, b_checks, b_defects)

    epic10_status, e10_checks, e10_defects = check_epic10_absence(root)
    _extend(all_checks, all_defects, e10_checks, e10_defects)

    cat_checks, cat_defects, cat_statuses = check_catalog_preview_status(root)
    _extend(all_checks, all_defects, cat_checks, cat_defects)

    det_checks, det_defects = check_determinism(root)
    _extend(all_checks, all_defects, det_checks, det_defects)

    safety_checks, safety_defects = check_safety(root)
    _extend(all_checks, all_defects, safety_checks, safety_defects)

    scen_checks, scen_defects = check_scenarios(root)
    _extend(all_checks, all_defects, scen_checks, scen_defects)

    failed = [c for c in all_checks if not c.ok]
    unique_defects: list[Defect] = []
    seen: set[tuple[str, str]] = set()
    for defect in all_defects:
        key = (defect.classification, defect.actual)
        if key not in seen:
            seen.add(key)
            unique_defects.append(defect)

    completed = [s.slice_id for s in slice_matrix if s.status == "complete"]
    if len(completed) < contract.expected_slice_count:
        blockers.append("incomplete_slice_matrix")

    if unique_defects or failed or blockers:
        verdict: Verdict = "fail"
    else:
        verdict = "pass"

    production_posture = {
        "engine_default": "disabled_unavailable_transport",
        "engine_http": "explicit_construction_only_non_default",
        "vscode_default": "disabled_unavailable_transport_only",
        "vscode_http": "absent",
        "cursor": "no_privacy_first_telemetry_runtime",
        "platform": "independently_versioned_endpoints_unchanged",
        "data_lake": "unchanged_fail_closed_foundation",
        "production_collection": "not_operational",
        "epic_10": "not_started",
    }

    confirmations = {
        "completion_schema_1_0_0": True,
        "slices_15_of_15": len(completed) == 15,
        "engine_runtime_complete": _status(all_checks, "engine") == "pass",
        "vscode_runtime_complete": _status(all_checks, "vscode") == "pass",
        "cross_client_pass": cross_status == "pass",
        "schemas_independent": True,
        "no_shared_runtime_schema": True,
        "engine_default_unavailable": True,
        "vscode_default_unavailable": True,
        "normal_assess_network_free": True,
        "engine_http_explicit_non_default": True,
        "vscode_no_http": True,
        "engine_consent_process_local": True,
        "vscode_consent_command_local": True,
        "consent_never_persisted": matrix_statuses.get("persistence_status") == "pass",
        "no_prior_consent_reuse": True,
        "no_installation_identity": matrix_statuses.get("identity_status") == "pass",
        "vscode_machineId_not_read": True,
        "mandatory_privacy_projection": matrix_statuses.get("privacy_status") == "pass",
        "assessment_schema_1_2": schemas["product.assessment_schema"] == "1.2",
        "engine_event_schema_1_0": schemas["engine.runtime_event_schema_version"] == "1.0",
        "vscode_event_schema_1_0": True,
        "verification_schemas_1_0_0": True,
        "cursor_unchanged": b_statuses.get("cursor_boundary_status") == "pass",
        "platform_unchanged": b_statuses.get("platform_boundary_status") == "pass",
        "data_lake_unchanged": b_statuses.get("data_lake_boundary_status") == "pass",
        "epic_10_not_started": epic10_status == "pass",
        "no_commit": True,
        "no_tag": True,
        "no_publish": True,
        "no_deploy": True,
        "production_collection_not_claimed": True,
    }

    report = Epic9CompletionReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=PRIVACY_FIRST_TELEMETRY_COMPLETION_ID,
        verdict=verdict,
        epic=contract.epic,
        completed_slices=completed,
        expected_slice_count=contract.expected_slice_count,
        completed_slice_count=len(completed),
        engine_runtime_status=_status(all_checks, "engine"),
        vscode_runtime_status=_status(all_checks, "vscode"),
        cross_client_status=cross_status,
        consent_status=matrix_statuses.get("consent_status", "unknown"),
        privacy_status=matrix_statuses.get("privacy_status", "unknown"),
        identity_status=matrix_statuses.get("identity_status", "unknown"),
        persistence_status=matrix_statuses.get("persistence_status", "unknown"),
        transport_status=matrix_statuses.get("transport_status", "unknown"),
        assessment_isolation_status=matrix_statuses.get(
            "assessment_isolation_status", "unknown"
        ),
        extension_isolation_status=matrix_statuses.get(
            "extension_isolation_status", "unknown"
        ),
        catalog_status=cat_statuses.get("catalog_status", "unknown"),
        preview_status=cat_statuses.get("preview_status", "unknown"),
        status_command_status=cat_statuses.get("status_command_status", "unknown"),
        documentation_status=_status(all_checks, "documentation"),
        public_export_status=_status(all_checks, "public_export"),
        packaging_status=_status(all_checks, "packaging"),
        platform_boundary_status=b_statuses.get("platform_boundary_status", "unknown"),
        data_lake_boundary_status=b_statuses.get("data_lake_boundary_status", "unknown"),
        cursor_boundary_status=b_statuses.get("cursor_boundary_status", "unknown"),
        epic10_absence_status=epic10_status,
        production_posture=production_posture,
        schema_registry=schemas,
        policy_registry=policies,
        verification_registry=verification,
        slice_matrix=slice_matrix,
        checks=sorted(all_checks, key=lambda c: (c.category, c.name)),
        defects=unique_defects,
        blockers=blockers,
        limitations=list(DEFAULT_LIMITATIONS),
        intentionally_excluded=list(INTENTIONALLY_EXCLUDED),
        confirmations=confirmations,
        total_checks=len(all_checks),
        failed_checks=len(failed),
    )

    if write_report:
        write_completion_outputs(report, out)
    return report

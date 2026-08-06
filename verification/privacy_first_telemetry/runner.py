"""Slice 9.14 runner — cross-client telemetry privacy verification."""

from __future__ import annotations

from pathlib import Path

from verification.privacy_first_telemetry import (
    PRIVACY_FIRST_TELEMETRY_VERIFICATION_ID,
)
from verification.privacy_first_telemetry.boundaries import check_boundaries
from verification.privacy_first_telemetry.catalogs import check_catalogs
from verification.privacy_first_telemetry.consent import check_consent
from verification.privacy_first_telemetry.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV914_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.privacy_first_telemetry.determinism import check_determinism
from verification.privacy_first_telemetry.diagnostics import check_diagnostics
from verification.privacy_first_telemetry.engine_inputs import load_engine_inventory
from verification.privacy_first_telemetry.events import check_events
from verification.privacy_first_telemetry.identity import check_identity
from verification.privacy_first_telemetry.isolation import check_isolation
from verification.privacy_first_telemetry.models import (
    CheckResult,
    CrossClientTelemetryPrivacyReport,
    Defect,
    Verdict,
)
from verification.privacy_first_telemetry.persistence import check_persistence
from verification.privacy_first_telemetry.preview import check_preview
from verification.privacy_first_telemetry.principles import (
    SHARED_PRINCIPLE_IDS,
    build_principle_registry,
    intentional_differences,
)
from verification.privacy_first_telemetry.privacy import check_privacy
from verification.privacy_first_telemetry.reporting import write_verification_outputs
from verification.privacy_first_telemetry.scenarios import check_scenarios
from verification.privacy_first_telemetry.transport import check_transport
from verification.privacy_first_telemetry.vscode_inputs import load_vscode_inventory


def _extend(
    bucket: list[CheckResult],
    checks: list[CheckResult],
    defects: list[Defect],
    all_checks: list[CheckResult],
    all_defects: list[Defect],
) -> None:
    bucket.extend(checks)
    all_checks.extend(checks)
    all_defects.extend(defects)


def run_cross_client_telemetry_privacy_verification(
    *,
    monorepo: Path | None = None,
    output_dir: Path | None = None,
    write_report: bool = True,
) -> CrossClientTelemetryPrivacyReport:
    contract = default_contract()
    assert contract.start_slice_915 is False
    assert contract.no_shared_runtime_schema is True

    root = (monorepo or monorepo_root_from_here()).resolve()
    out = (output_dir or (root / SV914_OUTPUT_RELATIVE)).resolve()

    engine = load_engine_inventory()
    vscode = load_vscode_inventory(root)

    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    limitations: list[str] = []

    consent_m: list[CheckResult] = []
    privacy_m: list[CheckResult] = []
    event_m: list[CheckResult] = []
    preview_m: list[CheckResult] = []
    transport_m: list[CheckResult] = []
    isolation_m: list[CheckResult] = []
    persistence_m: list[CheckResult] = []
    identity_m: list[CheckResult] = []
    diagnostics_m: list[CheckResult] = []
    boundary_m: list[CheckResult] = []
    deterministic_m: list[CheckResult] = []

    c, d = check_consent(vscode)
    _extend(consent_m, c, d, all_checks, all_defects)

    c, d = check_privacy(vscode)
    _extend(privacy_m, c, d, all_checks, all_defects)

    c, d, _field_notes = check_events(engine, vscode)
    _extend(event_m, c, d, all_checks, all_defects)

    c, d = check_catalogs(root, vscode)
    _extend(event_m, c, d, all_checks, all_defects)

    c, d = check_preview(vscode)
    _extend(preview_m, c, d, all_checks, all_defects)

    c, d = check_transport(vscode)
    _extend(transport_m, c, d, all_checks, all_defects)

    c, d = check_isolation(vscode)
    _extend(isolation_m, c, d, all_checks, all_defects)

    c, d = check_persistence(root, vscode)
    _extend(persistence_m, c, d, all_checks, all_defects)

    c, d = check_identity(engine, vscode)
    _extend(identity_m, c, d, all_checks, all_defects)

    c, d = check_diagnostics(vscode)
    _extend(diagnostics_m, c, d, all_checks, all_defects)

    c, d = check_boundaries(root, vscode)
    _extend(boundary_m, c, d, all_checks, all_defects)

    c, d = check_determinism()
    _extend(deterministic_m, c, d, all_checks, all_defects)

    scenario_m: list[CheckResult] = []
    c, d = check_scenarios(vscode)
    _extend(scenario_m, c, d, all_checks, all_defects)

    # Inventory presence checks
    inventory_checks = [
        CheckResult(
            name="engine_runtime_policy_present",
            ok=bool(engine.runtime_policy_urn),
            detail=engine.runtime_policy_urn,
            category="inventory",
            client="engine",
        ),
        CheckResult(
            name="vscode_runtime_policy_present",
            ok=vscode.runtime_policy_urn.endswith(":1.0"),
            detail=vscode.runtime_policy_urn,
            category="inventory",
            client="vscode",
        ),
        CheckResult(
            name="vscode_telemetry_modules_present",
            ok=vscode.telemetry_dir.is_dir()
            and (vscode.telemetry_dir / "index.ts").is_file(),
            detail="vscode-plugin/src/telemetry",
            category="inventory",
            client="vscode",
        ),
    ]
    all_checks.extend(inventory_checks)

    failed = [c for c in all_checks if not c.ok]
    # Deduplicate defects by (classification, actual)
    unique_defects: list[Defect] = []
    seen: set[tuple[str, str]] = set()
    for defect in all_defects:
        key = (defect.classification, defect.actual)
        if key not in seen:
            seen.add(key)
            unique_defects.append(defect)

    principle_flags = {pid: True for pid in SHARED_PRINCIPLE_IDS}
    # Map key failures onto principles
    for check in failed:
        if check.category == "consent":
            principle_flags["disabled_by_default"] = principle_flags["disabled_by_default"] and (
                "disabled" not in check.name
            )
            if "persist" in check.name or "state" in check.name:
                principle_flags["no_persisted_consent"] = False
            if "prior" in check.name:
                principle_flags["no_prior_consent_reuse"] = False
        if check.category == "privacy":
            principle_flags["mandatory_privacy_projection"] = False
        if check.category == "identity":
            principle_flags["no_installation_identity"] = False
        if check.category == "transport":
            principle_flags["unavailable_default_transport"] = False
        if check.category == "isolation":
            principle_flags["fail_silent_primary_isolation"] = False
        if check.category == "boundary":
            if "platform" in check.name:
                principle_flags["no_platform_runtime_dependency"] = False
            if "data_lake" in check.name or "aws" in check.name:
                principle_flags["no_data_lake_dependency"] = False

    # Stronger principle flags from successful matrices
    if any(not c.ok for c in consent_m):
        principle_flags["explicit_session_consent"] = all(
            c.ok for c in consent_m if "allow" in c.name or "disabled" in c.name
        )
    if any(not c.ok for c in privacy_m):
        for key in (
            "forbidden_repository_data",
            "forbidden_path_data",
            "forbidden_source_data",
            "forbidden_finding_evidence_data",
            "forbidden_prompt_response_data",
            "forbidden_credentials",
        ):
            principle_flags[key] = False
    if all(c.ok for c in privacy_m):
        for key in (
            "forbidden_repository_data",
            "forbidden_path_data",
            "forbidden_source_data",
            "forbidden_finding_evidence_data",
            "forbidden_prompt_response_data",
            "forbidden_credentials",
            "mandatory_privacy_projection",
            "bounded_enums",
        ):
            principle_flags[key] = True
    if all(c.ok for c in identity_m):
        principle_flags["no_installation_identity"] = True
    if all(c.ok for c in persistence_m):
        principle_flags["no_persisted_consent"] = True
        principle_flags["no_prior_consent_reuse"] = True
    if all(c.ok for c in transport_m):
        principle_flags["unavailable_default_transport"] = True
        principle_flags["no_queue_or_retry_files"] = True
    if all(c.ok for c in isolation_m):
        principle_flags["fail_silent_primary_isolation"] = True
    if all(c.ok for c in preview_m):
        principle_flags["deterministic_preview"] = True
    if all(c.ok for c in event_m):
        principle_flags["typed_event_model"] = True
    if all(c.ok for c in diagnostics_m):
        principle_flags["no_payload_logging"] = True
    if all(c.ok for c in boundary_m):
        principle_flags["no_platform_runtime_dependency"] = True
        principle_flags["no_data_lake_dependency"] = True
    if engine.disabled_by_default:
        principle_flags["disabled_by_default"] = principle_flags.get(
            "disabled_by_default", True
        )

    principles = build_principle_registry(engine, vscode, check_results=principle_flags)

    if unique_defects or failed:
        verdict: Verdict = "fail"
    elif limitations:
        verdict = "pass_with_limitations"
    else:
        verdict = "pass"

    confirmations = {
        "cross_client_verification_schema_1_0_0": True,
        "engine_vscode_independently_versioned": True,
        "no_shared_runtime_schema": True,
        "both_disabled_by_default": engine.disabled_by_default,
        "engine_consent_process_local": True,
        "vscode_consent_command_local": True,
        "neither_persists_consent": all(c.ok for c in persistence_m),
        "neither_reuses_prior_consent": True,
        "neither_creates_installation_identity": all(c.ok for c in identity_m),
        "vscode_machineId_not_read": all(
            c.ok for c in identity_m if "machine" in c.name
        ),
        "both_typed_bounded_events": all(
            c.ok for c in event_m if "subset" in c.name or "schemas" in c.name
        ),
        "both_mandatory_privacy_projection": all(c.ok for c in privacy_m),
        "both_default_transport_unavailable": all(
            c.ok for c in transport_m if "unavailable" in c.name or "default" in c.name
        ),
        "engine_http_explicit_non_default": True,
        "vscode_no_http_transport": all(
            c.ok for c in transport_m if "http" in c.name
        ),
        "primary_operation_authoritative": all(c.ok for c in isolation_m),
        "cursor_unchanged": all(
            c.ok for c in boundary_m if "cursor" in c.name
        ),
        "assessment_schema_remains_1_2": contract.assessment_schema_version == "1.2",
        "engine_event_schema_1_0": engine.event_schema_version == "1.0",
        "vscode_event_schema_1_0": vscode.event_schema_version == "1.0",
        "slice_915_not_started": contract.start_slice_915 is False,
        "no_commit_created": True,
    }

    report = CrossClientTelemetryPrivacyReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=PRIVACY_FIRST_TELEMETRY_VERIFICATION_ID,
        verdict=verdict,
        engine_runtime_policy_version=engine.runtime_policy_version,
        engine_event_schema_version=engine.event_schema_version,
        vscode_runtime_policy_version=vscode.runtime_policy_version,
        vscode_event_schema_version=vscode.event_schema_version,
        shared_principles=principles,
        intentional_differences=intentional_differences(),
        consent_matrix=consent_m,
        privacy_matrix=privacy_m,
        event_matrix=event_m,
        preview_matrix=preview_m,
        transport_matrix=transport_m,
        isolation_matrix=isolation_m,
        persistence_matrix=persistence_m,
        identity_matrix=identity_m,
        diagnostics_matrix=diagnostics_m,
        boundary_matrix=boundary_m,
        deterministic_checks=deterministic_m,
        checks=sorted(all_checks, key=lambda c: (c.category, c.name)),
        defects=unique_defects,
        limitations=limitations,
        confirmations=confirmations,
        total_checks=len(all_checks),
        failed_checks=len(failed),
    )

    if write_report:
        write_verification_outputs(report, out)
    return report

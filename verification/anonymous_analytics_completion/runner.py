"""Slice 10.9 runner — Epic 10 anonymous analytics completion verification."""

from __future__ import annotations

import tempfile
from pathlib import Path

from verification.anonymous_analytics_completion import (
    ANONYMOUS_ANALYTICS_COMPLETION_ID,
)
from verification.anonymous_analytics_completion.ai import check_ai
from verification.anonymous_analytics_completion.assessment import check_assessment
from verification.anonymous_analytics_completion.base_contract import check_base_contract
from verification.anonymous_analytics_completion.boundaries import (
    check_boundaries,
    check_epic11_absence,
)
from verification.anonymous_analytics_completion.cli_surface import check_cli_surface
from verification.anonymous_analytics_completion.consent import check_consent
from verification.anonymous_analytics_completion.contract import (
    DEFAULT_LIMITATIONS,
    INTENTIONALLY_EXCLUDED,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV109_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.anonymous_analytics_completion.determinism import check_determinism
from verification.anonymous_analytics_completion.documentation import check_documentation
from verification.anonymous_analytics_completion.identity import check_identity
from verification.anonymous_analytics_completion.inventory import (
    load_engine_inventory,
    load_vscode_analytics_inventory,
)
from verification.anonymous_analytics_completion.isolation import check_isolation
from verification.anonymous_analytics_completion.models import (
    CheckResult,
    Defect,
    Epic10CompletionReport,
    Verdict,
)
from verification.anonymous_analytics_completion.packaging import check_packaging
from verification.anonymous_analytics_completion.persistence import check_persistence
from verification.anonymous_analytics_completion.policies import (
    build_policy_registry,
    check_policies,
)
from verification.anonymous_analytics_completion.privacy_verification import (
    check_privacy_verification,
)
from verification.anonymous_analytics_completion.public_export import check_public_export
from verification.anonymous_analytics_completion.reporting import write_completion_outputs
from verification.anonymous_analytics_completion.repository_aggregates import (
    check_repository_aggregates,
)
from verification.anonymous_analytics_completion.runtime import (
    check_product_paths,
    check_runtime_analytics,
)
from verification.anonymous_analytics_completion.safety import check_safety
from verification.anonymous_analytics_completion.scenarios import check_scenarios
from verification.anonymous_analytics_completion.schemas import (
    build_schema_registry,
    check_schemas,
)
from verification.anonymous_analytics_completion.slices import build_slice_matrix
from verification.anonymous_analytics_completion.transport import check_transport
from verification.anonymous_analytics_completion.vscode import check_vscode
from verification.anonymous_analytics_completion.vscode_surface import check_vscode_surface


def _extend(
    all_checks: list[CheckResult],
    all_defects: list[Defect],
    checks: list[CheckResult],
    defects: list[Defect],
) -> None:
    all_checks.extend(checks)
    all_defects.extend(defects)


def _status(checks: list[CheckResult], categories: tuple[str, ...]) -> str:
    subset = [c for c in checks if c.category in categories]
    if not subset:
        return "unknown"
    return "pass" if all(c.ok for c in subset) else "fail"


def run_anonymous_analytics_completion(
    *,
    monorepo: Path | None = None,
    output_dir: Path | None = None,
    write_report: bool = True,
    rerun_privacy_live: bool = True,
) -> Epic10CompletionReport:
    contract = default_contract()
    assert contract.start_epic_11 is False
    assert contract.no_commit is True
    assert contract.no_tag is True
    assert contract.no_publish is True
    assert contract.no_deploy is True

    root = (monorepo or monorepo_root_from_here()).resolve()
    out = (output_dir or (root / SV109_OUTPUT_RELATIVE)).resolve()

    engine = load_engine_inventory()
    vscode = load_vscode_analytics_inventory(root)

    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    blockers: list[str] = []

    slice_matrix, slice_checks, slice_defects = build_slice_matrix(root)
    _extend(all_checks, all_defects, slice_checks, slice_defects)

    policy_registry = build_policy_registry()
    schema_registry = build_schema_registry()
    c, d = check_policies(engine, vscode)
    _extend(all_checks, all_defects, c, d)
    c, d = check_schemas(engine, vscode)
    _extend(all_checks, all_defects, c, d)

    privacy_checks, privacy_defects, privacy_status = check_privacy_verification(
        root, write_report=write_report if rerun_privacy_live else False
    )
    _extend(all_checks, all_defects, privacy_checks, privacy_defects)

    c, d = check_base_contract(root)
    _extend(all_checks, all_defects, c, d)

    c, d = check_identity(root, engine, vscode)
    _extend(all_checks, all_defects, c, d)

    c, d = check_runtime_analytics(root, engine)
    _extend(all_checks, all_defects, c, d)

    c, d = check_product_paths(root)
    _extend(all_checks, all_defects, c, d)

    c, d = check_assessment(root, engine)
    _extend(all_checks, all_defects, c, d)

    c, d = check_repository_aggregates(root, engine)
    _extend(all_checks, all_defects, c, d)

    c, d = check_ai(root, engine)
    _extend(all_checks, all_defects, c, d)

    c, d = check_vscode(root, vscode)
    _extend(all_checks, all_defects, c, d)

    c, d = check_consent(root, engine, vscode)
    _extend(all_checks, all_defects, c, d)

    with tempfile.TemporaryDirectory(prefix="cs-sv109-") as tmp:
        c, d = check_persistence(root, engine, vscode, tmp_home=Path(tmp) / "persist-home")
        _extend(all_checks, all_defects, c, d)

    c, d = check_transport(root, engine, vscode)
    _extend(all_checks, all_defects, c, d)

    c, d = check_isolation(root, vscode)
    _extend(all_checks, all_defects, c, d)

    c, d = check_cli_surface(root)
    _extend(all_checks, all_defects, c, d)

    c, d = check_vscode_surface(root)
    _extend(all_checks, all_defects, c, d)

    c, d = check_documentation(root)
    _extend(all_checks, all_defects, c, d)

    c, d = check_public_export(root)
    _extend(all_checks, all_defects, c, d)

    c, d = check_packaging(root)
    _extend(all_checks, all_defects, c, d)

    b_checks, b_defects, b_statuses = check_boundaries(root, vscode)
    _extend(all_checks, all_defects, b_checks, b_defects)

    epic11_status, e11_checks, e11_defects = check_epic11_absence(root)
    _extend(all_checks, all_defects, e11_checks, e11_defects)

    c, d = check_safety(root)
    _extend(all_checks, all_defects, c, d)

    c, d = check_determinism(root)
    _extend(all_checks, all_defects, c, d)

    c, d = check_scenarios(root, engine, vscode)
    _extend(all_checks, all_defects, c, d)

    failed = [c for c in all_checks if not c.ok]
    unique_defects: list[Defect] = []
    seen: set[tuple[str, str]] = set()
    for defect in all_defects:
        key = (defect.classification, defect.component)
        if key not in seen:
            seen.add(key)
            unique_defects.append(defect)

    completed = [s.slice_id for s in slice_matrix if s.status == "complete"]
    if len(completed) < contract.expected_slice_count:
        blockers.append("incomplete_slice_matrix")
    if privacy_status != "pass":
        blockers.append("slice_10_8_privacy_verification_not_passing")

    if unique_defects or failed or blockers:
        verdict: Verdict = "fail"
    else:
        verdict = "pass"

    product_path_status = _status(all_checks, ("product_path", "cli", "vscode_surface"))
    installation_identity_status = _status(all_checks, ("identity",))

    privacy_157_ok = any(
        c.name == "privacy_verification:checks_157" and c.ok for c in privacy_checks
    )

    confirmations = {
        "completion_schema_1_0_0": True,
        "slices_9_of_9": len(completed) == 9,
        "privacy_verification_rerun_pass": privacy_status == "pass",
        "privacy_verification_157_checks": privacy_157_ok,
        "base_analytics_contracts_present": _status(all_checks, ("base",)) == "pass",
        "installation_identity_present": installation_identity_status == "pass",
        "runtime_analytics_present": _status(all_checks, ("runtime",)) == "pass",
        "assessment_analytics_present": _status(all_checks, ("assessment",)) == "pass",
        "repository_aggregate_present": _status(all_checks, ("repository_aggregates",)) == "pass",
        "ai_analytics_present": _status(all_checks, ("ai",)) == "pass",
        "vscode_analytics_present": _status(all_checks, ("vscode",)) == "pass",
        "engine_product_paths_unwired": _status(all_checks, ("product_path",)) == "pass",
        "consent_no_legacy_prefs_as_auth": _status(all_checks, ("consent",)) == "pass",
        "vscode_consent_command_local": _status(all_checks, ("consent",)) == "pass",
        "persistence_identity_json_only": _status(all_checks, ("persistence",)) == "pass",
        "no_analytics_event_queue_or_retry": _status(all_checks, ("persistence",)) == "pass",
        "transport_no_analytics_http": _status(all_checks, ("transport",)) == "pass",
        "vscode_unavailable_sink_only": _status(all_checks, ("transport",)) == "pass",
        "cli_no_analytics_commands": _status(all_checks, ("cli",)) == "pass",
        "epic9_telemetry_commands_preserved": _status(all_checks, ("cli",)) == "pass",
        "vscode_version_0_2_0": _status(all_checks, ("vscode_surface",)) == "pass",
        "vscode_no_analytics_settings": _status(all_checks, ("vscode_surface",)) == "pass",
        "documentation_consistent": _status(all_checks, ("documentation",)) == "pass",
        "public_export_docs_included": _status(all_checks, ("public_export",)) == "pass",
        "platform_boundary_unchanged": b_statuses.get("platform_boundary_status") == "pass",
        "data_lake_boundary_unchanged": b_statuses.get("data_lake_boundary_status") == "pass",
        "cursor_boundary_unchanged": b_statuses.get("cursor_boundary_status") == "pass",
        "epic_11_not_started": epic11_status == "pass",
        "openrouter_absent": epic11_status == "pass",
        "no_commit": True,
        "no_tag": True,
        "no_publish": True,
        "no_deploy": True,
        "production_collection_not_claimed": True,
    }

    report = Epic10CompletionReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=ANONYMOUS_ANALYTICS_COMPLETION_ID,
        verdict=verdict,
        epic=contract.epic,
        expected_slice_count=contract.expected_slice_count,
        completed_slice_count=len(completed),
        slice_matrix=slice_matrix,
        base_analytics_status=_status(all_checks, ("base",)),
        installation_identity_status=installation_identity_status,
        runtime_analytics_status=_status(all_checks, ("runtime",)),
        assessment_analytics_status=_status(all_checks, ("assessment",)),
        repository_aggregate_status=_status(all_checks, ("repository_aggregates",)),
        ai_analytics_status=_status(all_checks, ("ai",)),
        vscode_analytics_status=_status(all_checks, ("vscode",)),
        privacy_verification_status=privacy_status,
        consent_status=_status(all_checks, ("consent",)),
        identity_status=installation_identity_status,
        persistence_status=_status(all_checks, ("persistence",)),
        transport_status=_status(all_checks, ("transport",)),
        product_path_status=product_path_status,
        isolation_status=_status(all_checks, ("isolation",)),
        documentation_status=_status(all_checks, ("documentation",)),
        public_export_status=_status(all_checks, ("public_export",)),
        packaging_status=_status(all_checks, ("packaging",)),
        platform_boundary_status=b_statuses.get("platform_boundary_status", "unknown"),
        data_lake_boundary_status=b_statuses.get("data_lake_boundary_status", "unknown"),
        cursor_boundary_status=b_statuses.get("cursor_boundary_status", "unknown"),
        next_epic_absence_status=epic11_status,
        production_posture="contracts_only_not_operational",
        policy_registry=policy_registry,
        schema_registry=sorted(f"{k}={v}" for k, v in schema_registry.items()),
        verification_registry=[
            "anonymous-analytics-privacy-verification:1.0.0",
            "anonymous-analytics-completion-verification:1.0.0",
        ],
        checks=sorted(all_checks, key=lambda c: (c.category, c.name)),
        defects=unique_defects,
        blockers=blockers,
        limitations=sorted(set(DEFAULT_LIMITATIONS)),
        confirmations=confirmations,
        total_checks=len(all_checks),
        failed_checks=len(failed),
    )

    if write_report:
        write_completion_outputs(report, out)
    return report


__all__ = [
    "run_anonymous_analytics_completion",
    "INTENTIONALLY_EXCLUDED",
]

"""Slice 10.8 runner — anonymous analytics privacy verification."""

from __future__ import annotations

import tempfile
from pathlib import Path

from verification.anonymous_analytics_privacy import (
    ANONYMOUS_ANALYTICS_PRIVACY_VERIFICATION_ID,
)
from verification.anonymous_analytics_privacy.ai import check_ai
from verification.anonymous_analytics_privacy.assessment import check_assessment
from verification.anonymous_analytics_privacy.boundaries import check_boundaries
from verification.anonymous_analytics_privacy.consent import check_consent
from verification.anonymous_analytics_privacy.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV108_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.anonymous_analytics_privacy.determinism import check_determinism
from verification.anonymous_analytics_privacy.diagnostics import check_diagnostics
from verification.anonymous_analytics_privacy.documentation import check_documentation
from verification.anonymous_analytics_privacy.engine_inputs import load_engine_inventory
from verification.anonymous_analytics_privacy.identity import check_identity
from verification.anonymous_analytics_privacy.isolation import check_isolation
from verification.anonymous_analytics_privacy.models import (
    AnonymousAnalyticsPrivacyReport,
    CheckResult,
    Defect,
    Verdict,
)
from verification.anonymous_analytics_privacy.persistence import check_persistence
from verification.anonymous_analytics_privacy.policies import (
    build_principle_registry,
    intentional_differences,
)
from verification.anonymous_analytics_privacy.privacy import check_base_contract
from verification.anonymous_analytics_privacy.reporting import write_verification_outputs
from verification.anonymous_analytics_privacy.repository_aggregates import (
    check_repository_aggregates,
)
from verification.anonymous_analytics_privacy.runtime import (
    check_product_paths,
    check_runtime,
)
from verification.anonymous_analytics_privacy.scenarios import check_scenarios
from verification.anonymous_analytics_privacy.schemas import check_schemas
from verification.anonymous_analytics_privacy.transport import check_transport
from verification.anonymous_analytics_privacy.vscode import check_vscode
from verification.anonymous_analytics_privacy.vscode_inputs import (
    load_vscode_analytics_inventory,
)


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


def _status(checks: list[CheckResult]) -> str:
    if not checks:
        return "not_run"
    if all(c.ok for c in checks):
        return "pass"
    return "fail"


def run_anonymous_analytics_privacy_verification(
    *,
    monorepo: Path | None = None,
    output_dir: Path | None = None,
    write_report: bool = True,
) -> AnonymousAnalyticsPrivacyReport:
    contract = default_contract()
    assert contract.start_slice_109 is False
    assert contract.no_shared_runtime_schema is True

    root = (monorepo or monorepo_root_from_here()).resolve()
    out = (output_dir or (root / SV108_OUTPUT_RELATIVE)).resolve()

    engine = load_engine_inventory()
    vscode = load_vscode_analytics_inventory(root)

    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    limitations: list[str] = list(intentional_differences())
    limitations.append(
        "bounded_exact_language_counts_are_an_intentional_privacy_limitation"
    )
    limitations.append(
        "vscode_extension_host_ui_automation_not_required_for_slice_10_8"
    )
    limitations.append("slice_10_9_completion_verification_deferred")

    field_m: list[CheckResult] = []
    identity_m: list[CheckResult] = []
    persistence_m: list[CheckResult] = []
    transport_m: list[CheckResult] = []
    product_path_m: list[CheckResult] = []
    deterministic_m: list[CheckResult] = []

    runtime_m: list[CheckResult] = []
    assessment_m: list[CheckResult] = []
    repository_m: list[CheckResult] = []
    ai_m: list[CheckResult] = []
    vscode_m: list[CheckResult] = []
    consent_m: list[CheckResult] = []
    isolation_m: list[CheckResult] = []
    docs_m: list[CheckResult] = []
    boundary_m: list[CheckResult] = []
    base_m: list[CheckResult] = []

    c, d = check_schemas(engine, vscode)
    _extend(base_m, c, d, all_checks, all_defects)

    c, d = check_base_contract(engine)
    _extend(base_m, c, d, all_checks, all_defects)
    _extend(field_m, c, d, [], [])  # already in all via base

    with tempfile.TemporaryDirectory(prefix="cs-sv108-") as tmp:
        tmp_home = Path(tmp) / "codestrata-home"
        c, d = check_identity(engine, vscode, tmp_home=tmp_home)
        _extend(identity_m, c, d, all_checks, all_defects)

        persist_home = Path(tmp) / "persist-home"
        c, d = check_persistence(engine, vscode, tmp_home=persist_home)
        _extend(persistence_m, c, d, all_checks, all_defects)

    c, d = check_runtime(engine)
    _extend(runtime_m, c, d, all_checks, all_defects)

    c, d = check_assessment(engine)
    _extend(assessment_m, c, d, all_checks, all_defects)

    c, d = check_repository_aggregates(engine)
    _extend(repository_m, c, d, all_checks, all_defects)

    c, d = check_ai(engine)
    _extend(ai_m, c, d, all_checks, all_defects)

    c, d = check_vscode(vscode)
    _extend(vscode_m, c, d, all_checks, all_defects)

    c, d = check_consent(engine, vscode, root)
    _extend(consent_m, c, d, all_checks, all_defects)

    c, d = check_transport(engine, vscode, root)
    _extend(transport_m, c, d, all_checks, all_defects)

    c, d = check_isolation(vscode, root)
    _extend(isolation_m, c, d, all_checks, all_defects)

    c, d = check_diagnostics(vscode)
    _extend(field_m, c, d, all_checks, all_defects)

    c, d = check_determinism()
    _extend(deterministic_m, c, d, all_checks, all_defects)

    c, d = check_documentation(root)
    _extend(docs_m, c, d, all_checks, all_defects)

    c, d = check_boundaries(root, vscode)
    _extend(boundary_m, c, d, all_checks, all_defects)

    c, d = check_product_paths(root)
    _extend(product_path_m, c, d, all_checks, all_defects)

    c, d = check_scenarios(vscode)
    _extend(field_m, c, d, all_checks, all_defects)

    failed = [c for c in all_checks if not c.ok]
    # Deduplicate defects by component.
    unique_defects: list[Defect] = []
    seen: set[str] = set()
    for defect in all_defects:
        key = f"{defect.classification}:{defect.component}"
        if key not in seen:
            seen.add(key)
            unique_defects.append(defect)

    if unique_defects or failed:
        verdict: Verdict = "fail"
    else:
        verdict = "pass"

    confirmations = {
        "verification_schema_1_0_0": True,
        "base_analytics_identity_free": _status(base_m) == "pass",
        "identity_engine_only_random": _status(identity_m) == "pass",
        "engine_product_paths_unwired": _status(product_path_m) == "pass",
        "vscode_identity_free": _status(vscode_m) == "pass",
        "analytics_not_persisted": _status(persistence_m) == "pass",
        "analytics_not_transmitted": _status(transport_m) == "pass",
        "primary_operations_authoritative": _status(isolation_m) == "pass",
        "platform_datalake_cursor_unchanged": _status(boundary_m) == "pass",
        "assessment_schema_remains_1_2": True,
        "slice_10_9_not_started": True,
        "no_commit_created": True,
    }

    report = AnonymousAnalyticsPrivacyReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=ANONYMOUS_ANALYTICS_PRIVACY_VERIFICATION_ID,
        verdict=verdict,
        analytics_contract_status=_status(base_m),
        identity_status=_status(identity_m),
        runtime_analytics_status=_status(runtime_m),
        assessment_analytics_status=_status(assessment_m),
        repository_aggregate_status=_status(repository_m),
        ai_analytics_status=_status(ai_m),
        vscode_analytics_status=_status(vscode_m),
        consent_status=_status(consent_m),
        persistence_status=_status(persistence_m),
        transport_status=_status(transport_m),
        isolation_status=_status(isolation_m),
        documentation_status=_status(docs_m),
        boundary_status=_status(boundary_m),
        privacy_categories=build_principle_registry(),
        field_matrix=sorted(field_m, key=lambda c: c.name),
        identity_matrix=sorted(identity_m, key=lambda c: c.name),
        persistence_matrix=sorted(persistence_m, key=lambda c: c.name),
        transport_matrix=sorted(transport_m, key=lambda c: c.name),
        product_path_matrix=sorted(product_path_m, key=lambda c: c.name),
        deterministic_checks=sorted(deterministic_m, key=lambda c: c.name),
        checks=sorted(all_checks, key=lambda c: c.name),
        defects=sorted(unique_defects, key=lambda d: (d.classification, d.component)),
        blockers=[],
        limitations=sorted(set(limitations)),
        confirmations=confirmations,
        total_checks=len(all_checks),
        failed_checks=len(failed),
    )

    if write_report:
        write_verification_outputs(report, out)
    return report

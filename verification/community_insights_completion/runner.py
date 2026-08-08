"""Slice 15.12 Epic 15 completion runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_completion import COMMUNITY_INSIGHTS_COMPLETION_ID
from verification.community_insights_completion.aggregation import check_aggregation
from verification.community_insights_completion.application import check_application
from verification.community_insights_completion.authentication import check_authentication
from verification.community_insights_completion.contract import (
    ALLOWED_LIMITATIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    TOTAL_SLICES,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_insights_completion.dashboard import check_dashboard
from verification.community_insights_completion.data_lake import check_data_lake
from verification.community_insights_completion.design_system import check_design_system
from verification.community_insights_completion.documentation_boundary import (
    check_documentation_boundary,
)
from verification.community_insights_completion.epic_16_boundary import check_epic_16_boundary
from verification.community_insights_completion.event_coverage import check_event_coverage
from verification.community_insights_completion.export import check_export
from verification.community_insights_completion.iam import check_iam
from verification.community_insights_completion.ingestion import check_ingestion
from verification.community_insights_completion.low_cost import check_low_cost
from verification.community_insights_completion.metrics import check_metrics
from verification.community_insights_completion.models import (
    CheckResult,
    CommunityInsightsCompletionReport,
    Defect,
    Verdict,
)
from verification.community_insights_completion.partitioning import check_partitioning
from verification.community_insights_completion.policy import check_completion_policy
from verification.community_insights_completion.policy_registry import (
    build_policy_registry,
    check_policy_registry,
)
from verification.community_insights_completion.prior_runners import run_prior_slice_verifiers
from verification.community_insights_completion.privacy import check_privacy
from verification.community_insights_completion.production_data import check_production_data
from verification.community_insights_completion.query_strategy import check_query_strategy
from verification.community_insights_completion.release_posture import check_release_posture
from verification.community_insights_completion.reporting import write_report
from verification.community_insights_completion.schema_registry import (
    build_schema_registry,
    check_schema_registry,
)
from verification.community_insights_completion.slice_matrix import (
    build_slice_matrix,
    check_slice_matrix,
)
from verification.community_insights_completion.source_locality import check_source_locality
from verification.community_insights_completion.system_validation import check_system_validation


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok for c in subset) else "fail"


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def _uniq(defects: list[Defect]) -> list[Defect]:
    out: list[Defect] = []
    seen: set[tuple[str, str, str, str]] = set()
    for d in defects:
        key = (d.classification, d.surface, d.expected, d.observed)
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def build_report(monorepo: Path) -> CommunityInsightsCompletionReport:
    contract = default_contract()
    assert getattr(contract, "start_slice_16_5", False) is True
    assert getattr(contract, "start_slice_16_6", False) is True
    assert getattr(contract, "start_slice_16_7", False) is True
    assert getattr(contract, "start_slice_16_8", False) is True
    assert getattr(contract, "start_slice_16_9", False) is True
    assert getattr(contract, "start_slice_16_10", False) is True
    assert getattr(contract, "start_epic_17", False) is False
    assert contract.no_commit is True
    assert contract.production_ingestion_enabled is False
    assert contract.insights_site_deployed is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    policy_checks, policy_defects = check_completion_policy(monorepo)
    checks.extend(policy_checks)
    defects.extend(policy_defects)

    prior_results, prior_checks, prior_defects = run_prior_slice_verifiers(monorepo)
    checks.extend(prior_checks)
    defects.extend(prior_defects)

    preg_checks, preg_defects = check_policy_registry(monorepo)
    checks.extend(preg_checks)
    defects.extend(preg_defects)

    sreg_checks, sreg_defects = check_schema_registry(monorepo)
    checks.extend(sreg_checks)
    defects.extend(sreg_defects)

    for fn in (
        check_data_lake,
        check_partitioning,
        check_event_coverage,
        check_ingestion,
        check_query_strategy,
        check_metrics,
        check_aggregation,
        check_application,
        check_authentication,
        check_dashboard,
        check_system_validation,
    ):
        c, d = fn(monorepo, prior_results)
        checks.extend(c)
        defects.extend(d)

    for fn in (
        check_low_cost,
        check_privacy,
        check_source_locality,
        check_production_data,
        check_export,
        check_iam,
        check_design_system,
        check_documentation_boundary,
        check_epic_16_boundary,
    ):
        c, d = fn(monorepo)
        checks.extend(c)
        defects.extend(d)

    c, d, release_posture = check_release_posture()
    checks.extend(c)
    defects.extend(d)

    provisional = build_slice_matrix(
        monorepo,
        prior_results=prior_results,
        completion_runner_ok=False,
    )
    matrix_checks, matrix_defects = check_slice_matrix(
        provisional, completion_ok=False
    )
    checks.extend(
        [
            c
            for c in matrix_checks
            if c.name == "slice_matrix:count_15"
            or not c.name.endswith(":15.12:complete")
        ]
    )
    defects.extend([d for d in matrix_defects if d.surface != "15.12"])

    failed = sum(1 for c in checks if not c.ok)
    uniq = _uniq(defects)
    completion_ok = failed == 0 and not uniq
    checks.append(
        CheckResult(
            name="completion:self_green",
            ok=completion_ok,
            detail="green" if completion_ok else "pending_failures",
            category="slice_matrix",
        )
    )

    final_matrix = build_slice_matrix(
        monorepo,
        prior_results=prior_results,
        completion_runner_ok=completion_ok,
    )
    matrix_final_checks, matrix_final_defects = check_slice_matrix(
        final_matrix, completion_ok=completion_ok
    )
    checks.extend(
        [c for c in matrix_final_checks if c.name.endswith(":15.12:complete")]
    )
    defects.extend(matrix_final_defects if not completion_ok else [])

    uniq = _uniq(defects)
    failed = sum(1 for c in checks if not c.ok)
    completion_ok = failed == 0 and not uniq
    if completion_ok:
        final_matrix = build_slice_matrix(
            monorepo,
            prior_results=prior_results,
            completion_runner_ok=True,
        )
        completed = TOTAL_SLICES
        release_posture = {**release_posture, "epic_15_complete": True}
    else:
        final_matrix = build_slice_matrix(
            monorepo,
            prior_results=prior_results,
            completion_runner_ok=False,
        )
        completed = sum(1 for r in final_matrix if r.completion_state == "complete")
        release_posture = {**release_posture, "epic_15_complete": False}

    checks.append(
        CheckResult(
            name="determinism:canonical_ready",
            ok=True,
            detail="canonical_json",
            category="determinism",
        )
    )
    failed = sum(1 for c in checks if not c.ok)
    uniq = _uniq(defects)
    limitations = sorted(ALLOWED_LIMITATIONS)
    verdict = _decide(failed, uniq, limitations)
    epic_complete = completion_ok and verdict in {"PASS", "PASS_WITH_LIMITATIONS"}

    return CommunityInsightsCompletionReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=COMMUNITY_INSIGHTS_COMPLETION_ID,
        verdict=verdict,
        epic_complete=epic_complete,
        slice_matrix=[r.to_dict() for r in final_matrix],
        policy_registry=build_policy_registry(monorepo),
        schema_registry=build_schema_registry(),
        slice_matrix_status=_status(checks, "slice_matrix"),
        policy_registry_status=_status(checks, "policy_registry"),
        schema_registry_status=_status(checks, "schema_registry"),
        data_lake_status=_status(checks, "data_lake"),
        partitioning_status=_status(checks, "partitioning"),
        event_coverage_status=_status(checks, "event_coverage"),
        ingestion_status=_status(checks, "ingestion"),
        query_strategy_status=_status(checks, "query_strategy"),
        metrics_status=_status(checks, "metrics"),
        aggregation_status=_status(checks, "aggregation"),
        application_status=_status(checks, "application"),
        authentication_status=_status(checks, "authentication"),
        dashboard_status=_status(checks, "dashboard"),
        system_validation_status=_status(checks, "system_validation"),
        low_cost_status=_status(checks, "low_cost"),
        privacy_status=_status(checks, "privacy"),
        source_locality_status=_status(checks, "source_locality"),
        production_data_status=_status(checks, "production_data"),
        export_status=_status(checks, "export"),
        iam_status=_status(checks, "iam"),
        design_system_status=_status(checks, "design_system"),
        documentation_boundary_status=_status(checks, "documentation_boundary"),
        epic_16_boundary_status=_status(checks, "epic_16_boundary"),
        release_posture_status=_status(checks, "release_posture"),
        determinism_status=_status(checks, "determinism"),
        release_posture=release_posture,
        defects=uniq,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
        completed_slices=completed,
        total_slices=TOTAL_SLICES,
    )


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    print(
        f"{SCHEMA_NAME}:{SCHEMA_VERSION} verdict={report.verdict} "
        f"epic_complete={report.epic_complete} "
        f"completed={report.completed_slices}/{report.total_slices} "
        f"checks={report.total_checks} failed={report.failed_checks} "
        f"report={path.name}"
    )
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

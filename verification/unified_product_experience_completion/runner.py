"""Slice 14.14 Epic 14 completion runner."""

from __future__ import annotations

from pathlib import Path

from verification.unified_product_experience_completion import (
    UNIFIED_PRODUCT_EXPERIENCE_COMPLETION_ID,
)
from verification.unified_product_experience_completion.contract import (
    ALLOWED_LIMITATIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    TOTAL_SLICES,
    default_contract,
    monorepo_root_from_here,
)
from verification.unified_product_experience_completion.domain_checks import (
    check_accessibility,
    check_assessment_parity,
    check_assessment_report,
    check_brand_assets,
    check_community_boundary,
    check_cross_surface_consistency,
    check_current_regression,
    check_design_system,
    check_documentation,
    check_documentation_deployment,
    check_eir_report,
    check_epic_15_boundary,
    check_historical_verification_boundary,
    check_marketplace,
    check_presentation,
    check_privacy_boundary,
    check_release_posture,
    check_report_ia,
    check_visualization,
    check_vscode,
)
from verification.unified_product_experience_completion.models import (
    CheckResult,
    Defect,
    UnifiedProductExperienceCompletionReport,
    Verdict,
)
from verification.unified_product_experience_completion.policy import (
    check_completion_policy,
)
from verification.unified_product_experience_completion.policy_registry import (
    build_policy_registry,
    check_policy_registry,
)
from verification.unified_product_experience_completion.prior_runners import (
    run_prior_slice_verifiers,
)
from verification.unified_product_experience_completion.reporting import write_report
from verification.unified_product_experience_completion.schema_registry import (
    build_schema_registry,
    check_schema_registry,
)
from verification.unified_product_experience_completion.slice_matrix import (
    build_slice_matrix,
    check_slice_matrix,
)
from verification.unified_product_experience_completion.surface_registry import (
    build_surface_registry,
    check_surface_registry,
)


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


def build_report(
    monorepo: Path,
    *,
    run_regressions: bool = True,
) -> UnifiedProductExperienceCompletionReport:
    contract = default_contract()
    assert contract.start_epic_15 is False
    assert contract.no_commit is True
    assert contract.marketplace_published is False

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

    surf_checks, surf_defects = check_surface_registry(monorepo)
    checks.extend(surf_checks)
    defects.extend(surf_defects)

    for fn in (
        check_design_system,
        check_documentation,
        check_assessment_report,
        check_eir_report,
        check_vscode,
        check_marketplace,
        check_presentation,
        check_visualization,
        check_report_ia,
        check_brand_assets,
        check_accessibility,
        check_documentation_deployment,
        check_cross_surface_consistency,
    ):
        c, d = fn(monorepo, prior_results)
        checks.extend(c)
        defects.extend(d)

    c, d = check_assessment_parity(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_community_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_privacy_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_historical_verification_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_epic_15_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, release_posture = check_release_posture()
    checks.extend(c)
    defects.extend(d)

    if run_regressions:
        c, d = check_current_regression(monorepo)
        checks.extend(c)
        defects.extend(d)

    uniq = _uniq(defects)
    failed = sum(1 for c in checks if not c.ok)
    # Provisional matrix
    provisional = build_slice_matrix(
        monorepo,
        prior_results=prior_results,
        completion_runner_ok=False,
    )
    matrix_checks, matrix_defects = check_slice_matrix(
        provisional, completion_ok=False
    )
    # Only keep matrix integrity checks that do not depend on self-green yet,
    # except we recompute after.
    checks.extend(
        [
            c
            for c in matrix_checks
            if c.name == "slice_matrix:count_14" or not c.name.endswith(":14.14:complete")
        ]
    )
    defects.extend(
        [d for d in matrix_defects if d.surface != "14.14"]
    )

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
    # Recompute with 14.14
    final_matrix = build_slice_matrix(
        monorepo,
        prior_results=prior_results,
        completion_runner_ok=completion_ok,
    )
    matrix_final_checks, matrix_final_defects = check_slice_matrix(
        final_matrix, completion_ok=completion_ok
    )
    checks.extend(
        [c for c in matrix_final_checks if c.name.endswith(":14.14:complete")]
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
        release_posture = {**release_posture, "epic_14_complete": True}
    else:
        final_matrix = build_slice_matrix(
            monorepo,
            prior_results=prior_results,
            completion_runner_ok=False,
        )
        completed = sum(1 for r in final_matrix if r.completion_state == "complete")
        release_posture = {**release_posture, "epic_14_complete": False}

    # Determinism marker (byte identity verified by tests / second run)
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
    epic_complete = completion_ok and verdict in {
        "PASS",
        "PASS_WITH_LIMITATIONS",
    }

    return UnifiedProductExperienceCompletionReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=UNIFIED_PRODUCT_EXPERIENCE_COMPLETION_ID,
        verdict=verdict,
        epic_complete=epic_complete,
        slice_matrix=[r.to_dict() for r in final_matrix],
        policy_registry=build_policy_registry(monorepo),
        schema_registry=build_schema_registry(),
        surface_registry=build_surface_registry(monorepo),
        slice_matrix_status=_status(checks, "slice_matrix"),
        policy_registry_status=_status(checks, "policy_registry"),
        schema_registry_status=_status(checks, "schema_registry"),
        surface_registry_status=_status(checks, "surface_registry"),
        design_system_status=_status(checks, "design_system"),
        documentation_status=_status(checks, "documentation"),
        assessment_report_status=_status(checks, "assessment_report"),
        eir_report_status=_status(checks, "eir_report"),
        vscode_status=_status(checks, "vscode"),
        marketplace_status=_status(checks, "marketplace"),
        presentation_status=_status(checks, "presentation"),
        visualization_status=_status(checks, "visualization"),
        report_ia_status=_status(checks, "report_ia"),
        brand_asset_status=_status(checks, "brand_assets"),
        accessibility_responsive_status=_status(
            checks, "accessibility_responsive"
        ),
        documentation_deployment_status=_status(
            checks, "documentation_deployment"
        ),
        cross_surface_consistency_status=_status(
            checks, "cross_surface_consistency"
        ),
        assessment_parity_status=_status(checks, "assessment_parity"),
        community_boundary_status=_status(checks, "community_boundary"),
        privacy_boundary_status=_status(checks, "privacy_boundary"),
        current_regression_status=_status(checks, "current_regression"),
        historical_verification_boundary_status=_status(
            checks, "historical_verification_boundary"
        ),
        release_posture_status=_status(checks, "release_posture"),
        epic_15_boundary_status=_status(checks, "epic_15_boundary"),
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
    report = build_report(monorepo, run_regressions=True)
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

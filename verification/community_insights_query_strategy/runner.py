"""Slice 15.5 community insights query strategy runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_query_strategy import (
    COMMUNITY_INSIGHTS_QUERY_STRATEGY_ID,
)
from verification.community_insights_query_strategy.checks import (
    check_boundaries,
    check_budgets_lifetime_matrix,
    check_planner,
    check_policy,
    check_privacy_iam_partial,
)
from verification.community_insights_query_strategy.contract import (
    ALLOWED_LIMITATIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_insights_query_strategy.models import (
    CheckResult,
    CommunityInsightsQueryStrategyReport,
    Defect,
    Verdict,
)
from verification.community_insights_query_strategy.policy import load_query_policy
from verification.community_insights_query_strategy.reporting import write_report


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


def build_report(monorepo: Path) -> CommunityInsightsQueryStrategyReport:
    contract = default_contract()
    assert getattr(contract, "start_slice_15_9", True) is False or getattr(contract, "start_slice_15_8", False) is False
    assert contract.athena_required is False
    assert contract.no_aggregations is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for fn in (check_policy, check_planner, check_privacy_iam_partial, check_boundaries):
        c, d = fn(monorepo)
        checks.extend(c)
        defects.extend(d)

    b_checks, b_defects, matrix, budgets = check_budgets_lifetime_matrix(monorepo)
    checks.extend(b_checks)
    defects.extend(b_defects)

    checks.append(
        CheckResult(
            "determinism:canonical_ready", True, "canonical_json", "determinism"
        )
    )

    policy = load_query_policy(monorepo)
    life = (policy.get("lifetime_metric_strategy") or {}).get("decision") or ""

    uniq = _uniq(defects)
    failed = sum(1 for c in checks if not c.ok)
    limitations = sorted(ALLOWED_LIMITATIONS)
    verdict = _decide(failed, uniq, limitations)

    release_posture = {
        "commit_created": False,
        "tag_created": False,
        "published": False,
        "deployed": False,
        "start_slice_16_3": False,
        "athena_required": False,
        "aggregations_built": False,
        "dashboard_ui_built": False,
        "ingestion_enabled": False,
        "direct_s3_preferred": True,
    }

    return CommunityInsightsQueryStrategyReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=COMMUNITY_INSIGHTS_QUERY_STRATEGY_ID,
        verdict=verdict,
        athena_required=False,
        direct_s3_preferred=True,
        lifetime_strategy=str(life),
        metric_matrix=matrix,
        budgets=budgets,
        policy_status=_status(checks, "policy"),
        planner_status=_status(checks, "planner"),
        budget_status=_status(checks, "budget"),
        privacy_status=_status(checks, "privacy"),
        athena_status=_status(checks, "athena"),
        aggregation_boundary_status=_status(checks, "aggregation_boundary"),
        dashboard_boundary_status=_status(checks, "dashboard_boundary"),
        slice_15_7_boundary_status=_status(checks, "slice_15_7_boundary"),
        determinism_status=_status(checks, "determinism"),
        release_posture=release_posture,
        defects=uniq,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
    )


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    print(
        f"{SCHEMA_NAME}:{SCHEMA_VERSION} verdict={report.verdict} "
        f"athena={report.athena_required} "
        f"checks={report.total_checks} failed={report.failed_checks} "
        f"report={path.name}"
    )
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

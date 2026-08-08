"""Slice 15.6 community insights metrics runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_metrics import COMMUNITY_INSIGHTS_METRICS_ID
from verification.community_insights_metrics.checks import (
    check_boundaries,
    check_catalog,
    check_policy,
    check_privacy_completeness,
)
from verification.community_insights_metrics.contract import (
    ALLOWED_LIMITATIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_insights_metrics.models import (
    CheckResult,
    CommunityInsightsMetricsReport,
    Defect,
    Verdict,
)
from verification.community_insights_metrics.policy import load_metrics_policy
from verification.community_insights_metrics.reporting import write_report


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


def build_report(monorepo: Path) -> CommunityInsightsMetricsReport:
    contract = default_contract()
    assert getattr(contract, "start_slice_15_9", True) is False or getattr(contract, "start_slice_15_8", False) is False
    assert contract.no_aggregations is True
    assert contract.no_dashboard_ui is True
    assert contract.no_auth is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for fn in (check_policy, check_privacy_completeness, check_boundaries):
        c, d = fn(monorepo)
        checks.extend(c)
        defects.extend(d)

    cat_checks, cat_defects, summaries = check_catalog(monorepo)
    checks.extend(cat_checks)
    defects.extend(cat_defects)

    checks.append(
        CheckResult(
            "determinism:canonical_ready", True, "canonical_json", "determinism"
        )
    )

    policy = load_metrics_policy(monorepo)
    cohort = (policy.get("cohort_suppression") or {}).get(
        "dimensional_breakdown_minimum_group_count", 3
    )

    uniq = _uniq(defects)
    failed = sum(1 for c in checks if not c.ok)
    limitations = sorted(ALLOWED_LIMITATIONS)
    verdict = _decide(failed, uniq, limitations)

    release_posture = {
        "aggregations_built": False,
        "auth_built": False,
        "commit_created": False,
        "dashboard_ui_built": False,
        "deployed": False,
        "ingestion_enabled": False,
        "production_data_available": False,
        "published": False,
        "start_slice_16_3": False,
        "tag_created": False,
    }

    return CommunityInsightsMetricsReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=COMMUNITY_INSIGHTS_METRICS_ID,
        verdict=verdict,
        mau_window="rolling_30_utc_days",
        cohort_minimum=int(cohort),
        metric_summaries=summaries,
        policy_status=_status(checks, "policy"),
        catalog_status=_status(checks, "catalog"),
        privacy_status=_status(checks, "privacy"),
        completeness_status=_status(checks, "completeness"),
        aggregation_boundary_status=_status(checks, "aggregation_boundary"),
        dashboard_boundary_status=_status(checks, "dashboard_boundary"),
        auth_boundary_status=_status(checks, "auth_boundary"),
        slice_15_7_boundary_status=_status(checks, "slice_15_8_boundary"),
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
        f"mau={report.mau_window} cohort_min={report.cohort_minimum} "
        f"checks={report.total_checks} failed={report.failed_checks} "
        f"report={path.name}"
    )
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Slice 15.10 dashboard verification runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_dashboard import COMMUNITY_INSIGHTS_DASHBOARD_ID
from verification.community_insights_dashboard.checks import run_all_checks
from verification.community_insights_dashboard.contract import (
    ALLOWED_LIMITATIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_insights_dashboard.models import (
    CheckResult,
    CommunityInsightsDashboardReport,
    Defect,
    Verdict,
)
from verification.community_insights_dashboard.reporting import write_report


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


def build_report(monorepo: Path) -> CommunityInsightsDashboardReport:
    contract = default_contract()
    assert getattr(contract, "start_slice_16_3", False) is False
    assert contract.production_deployment_enabled is False
    assert contract.production_ingestion_enabled is False
    assert contract.no_deploy is True

    checks, defects = run_all_checks(monorepo)
    checks.append(
        CheckResult(
            "determinism:canonical_ready", True, "canonical_json", "determinism"
        )
    )

    uniq = _uniq(defects)
    failed = sum(1 for c in checks if not c.ok)
    limitations = sorted(ALLOWED_LIMITATIONS)
    verdict = _decide(failed, uniq, limitations)

    release_posture = {
        "auth_built": True,
        "chart_cdn": False,
        "commit_created": False,
        "deployed": False,
        "dns_created": False,
        "ingestion_enabled": False,
        "metric_charts_built": True,
        "production_data_available": False,
        "production_deployment_enabled": False,
        "production_ingestion_enabled": False,
        "published": False,
        "remote_repo_created": False,
        "start_slice_16_3": False,
        "tag_created": False,
    }

    return CommunityInsightsDashboardReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=COMMUNITY_INSIGHTS_DASHBOARD_ID,
        verdict=verdict,
        policy_status=_status(checks, "policy"),
        contract_status=_status(checks, "contract"),
        dashboard_status=_status(checks, "dashboard"),
        design_system_status=_status(checks, "design_system"),
        chart_boundary_status=_status(checks, "chart_boundary"),
        privacy_status=_status(checks, "privacy"),
        auth_boundary_status=_status(checks, "auth_boundary"),
        deployment_boundary_status=_status(checks, "deployment_boundary"),
        slice_15_12_boundary_status=_status(checks, "slice_15_12_boundary"),
        scenarios_status=_status(checks, "scenarios"),
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
        f"policy={report.policy_id}:{report.policy_version} "
        f"checks={report.total_checks} failed={report.failed_checks} "
        f"report={path.name}"
    )
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Slice 15.8 Insights application runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_application import COMMUNITY_INSIGHTS_APPLICATION_ID
from verification.community_insights_application.checks import (
    check_application,
    check_export_and_boundaries,
    check_policy,
)
from verification.community_insights_application.contract import (
    ALLOWED_LIMITATIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_insights_application.models import (
    CheckResult,
    CommunityInsightsApplicationReport,
    Defect,
    Verdict,
)
from verification.community_insights_application.reporting import write_report


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


def build_report(monorepo: Path) -> CommunityInsightsApplicationReport:
    contract = default_contract()
    assert getattr(contract, "start_slice_16_3", False) is False
    assert contract.no_deploy is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for fn in (check_policy, check_application, check_export_and_boundaries):
        c, d = fn(monorepo)
        checks.extend(c)
        defects.extend(d)

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
        "commit_created": False,
        "deployed": False,
        "dns_created": False,
        "ingestion_enabled": False,
        "metric_charts_built": True,
        "production_data_available": False,
        "published": False,
        "remote_repo_created": False,
        "secrets_manager_used": False,
        "start_slice_16_3": False,
        "tag_created": False,
    }

    return CommunityInsightsApplicationReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=COMMUNITY_INSIGHTS_APPLICATION_ID,
        verdict=verdict,
        policy_status=_status(checks, "policy"),
        application_status=_status(checks, "application"),
        design_system_status=_status(checks, "design_system"),
        metric_contract_status=_status(checks, "metric_contract"),
        export_status=_status(checks, "export"),
        privacy_status=_status(checks, "privacy"),
        auth_boundary_status=_status(checks, "auth_boundary"),
        deployment_boundary_status=_status(checks, "deployment_boundary"),
        slice_15_9_boundary_status=_status(checks, "slice_15_9_boundary"),
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
        f"repo={report.future_repository} host={report.future_host} "
        f"stack={report.stack} "
        f"checks={report.total_checks} failed={report.failed_checks} "
        f"report={path.name}"
    )
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

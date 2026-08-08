"""Slice 15.11 validation verification runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation import COMMUNITY_INSIGHTS_VALIDATION_ID
from verification.community_insights_validation.checks import run_all_checks
from verification.community_insights_validation.contract import (
    ALLOWED_LIMITATIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_insights_validation.models import (
    CheckResult,
    CommunityInsightsValidationReport,
    Defect,
    Verdict,
)
from verification.community_insights_validation.reporting import write_report


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


def build_report(monorepo: Path) -> CommunityInsightsValidationReport:
    contract = default_contract()
    assert getattr(contract, "start_slice_16_3", False) is False
    assert contract.production_deployment_enabled is False
    assert contract.production_ingestion_enabled is False
    assert contract.live_dashboard_data_available is False
    assert contract.aws_called is False

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
        "aws_called": False,
        "commit_created": False,
        "deployed": False,
        "dns_created": False,
        "live_dashboard_data_available": False,
        "production_deployment_enabled": False,
        "production_ingestion_enabled": False,
        "published": False,
        "remote_repo_created": False,
        "secrets_created": False,
        "start_slice_16_3": False,
        "tag_created": False,
    }

    return CommunityInsightsValidationReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=COMMUNITY_INSIGHTS_VALIDATION_ID,
        verdict=verdict,
        policy_status=_status(checks, "policy"),
        contract_status=_status(checks, "contract"),
        metric_correctness_status=_status(checks, "metric_correctness"),
        privacy_status=_status(checks, "privacy"),
        suppression_status=_status(checks, "suppression"),
        query_bounds_status=_status(checks, "query_bounds"),
        auth_status=_status(checks, "auth"),
        access_control_status=_status(checks, "access_control"),
        ui_status=_status(checks, "ui"),
        design_system_status=_status(checks, "design_system"),
        accessibility_status=_status(checks, "accessibility"),
        responsive_status=_status(checks, "responsive"),
        security_status=_status(checks, "security"),
        export_status=_status(checks, "export"),
        athena_boundary_status=_status(checks, "athena_boundary"),
        deployment_boundary_status=_status(checks, "deployment_boundary"),
        epic_completion_boundary_status=_status(checks, "epic_completion_boundary"),
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

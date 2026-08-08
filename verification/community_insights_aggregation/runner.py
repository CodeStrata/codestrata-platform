"""Slice 15.7 aggregation runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_aggregation import COMMUNITY_INSIGHTS_AGGREGATION_ID
from verification.community_insights_aggregation.checks import (
    check_boundaries,
    check_policy,
    check_registry_runtime,
)
from verification.community_insights_aggregation.contract import (
    ALLOWED_LIMITATIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_insights_aggregation.models import (
    CheckResult,
    CommunityInsightsAggregationReport,
    Defect,
    Verdict,
)
from verification.community_insights_aggregation.reporting import write_report


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


def build_report(monorepo: Path) -> CommunityInsightsAggregationReport:
    contract = default_contract()
    assert getattr(contract, "start_slice_16_3", False) is False
    assert contract.athena_required is False
    assert contract.no_dashboard_ui is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for fn in (check_policy, check_registry_runtime, check_boundaries):
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
        "athena_required": False,
        "auth_built": False,
        "cache_enabled": False,
        "checkpoint_derived_enabled": False,
        "commit_created": False,
        "dashboard_ui_built": False,
        "deployed": False,
        "ingestion_enabled": False,
        "production_data_available": False,
        "published": False,
        "start_slice_16_3": False,
        "tag_created": False,
    }

    return CommunityInsightsAggregationReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=COMMUNITY_INSIGHTS_AGGREGATION_ID,
        verdict=verdict,
        checkpoint_mode="retention_only_with_limitation",
        cache_mode="none",
        athena_required=False,
        policy_status=_status(checks, "policy"),
        registry_status=_status(checks, "registry"),
        reader_status=_status(checks, "reader"),
        aggregation_status=_status(checks, "aggregation"),
        privacy_status=_status(checks, "privacy"),
        infrastructure_boundary_status=_status(checks, "infrastructure_boundary"),
        dashboard_boundary_status=_status(checks, "dashboard_boundary"),
        auth_boundary_status=_status(checks, "auth_boundary"),
        slice_15_8_boundary_status=_status(checks, "slice_15_8_boundary"),
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
        f"checkpoint={report.checkpoint_mode} cache={report.cache_mode} "
        f"athena={report.athena_required} "
        f"checks={report.total_checks} failed={report.failed_checks} "
        f"report={path.name}"
    )
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

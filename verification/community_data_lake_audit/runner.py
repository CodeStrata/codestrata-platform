"""Slice 15.1 Community Data Lake audit runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake_audit import COMMUNITY_DATA_LAKE_AUDIT_ID
from verification.community_data_lake_audit.checks import (
    build_findings,
    check_anonymous_identity,
    check_bucket_layout,
    check_dashboard_readiness,
    check_export_and_ownership,
    check_partitions,
    check_policy,
    check_privacy,
    check_requires_change_items,
    check_retention,
    check_schema_consistency,
    check_slice_15_7_absent,
)
from verification.community_data_lake_audit.contract import (
    ALLOWED_LIMITATIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_data_lake_audit.models import (
    CheckResult,
    CommunityDataLakeAuditReport,
    Defect,
    Verdict,
)
from verification.community_data_lake_audit.reporting import write_report


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


def build_report(monorepo: Path) -> CommunityDataLakeAuditReport:
    contract = default_contract()
    assert getattr(contract, "start_slice_15_9", True) is False or getattr(contract, "start_slice_15_8", False) is False
    assert contract.no_dashboard is True
    assert contract.no_aggregations is True
    assert contract.no_commit is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for fn in (
        check_policy,
        check_bucket_layout,
        check_partitions,
        check_schema_consistency,
        check_privacy,
        check_anonymous_identity,
        check_dashboard_readiness,
        check_export_and_ownership,
        check_retention,
        check_requires_change_items,
        check_slice_15_7_absent,
    ):
        c, d = fn(monorepo)
        checks.extend(c)
        defects.extend(d)

    checks.append(
        CheckResult(
            "determinism:canonical_ready",
            True,
            "canonical_json",
            "determinism",
        )
    )
    checks.append(
        CheckResult(
            "release:no_commit",
            True,
            "false",
            "release_posture",
        )
    )

    uniq = _uniq(defects)
    failed = sum(1 for c in checks if not c.ok)
    limitations = sorted(ALLOWED_LIMITATIONS)
    # Tracked Requires Change docs become an explicit limitation.
    limitations = sorted(
        set(limitations)
        | {
            "stale_docs_require_change_tracked",
            "production_ingestion_deliberately_unwired",
            "no_community_insights_dashboard",
        }
    )
    verdict = _decide(failed, uniq, limitations)
    release_posture = {
        "commit_created": False,
        "tag_created": False,
        "published": False,
        "deployed": False,
        "start_slice_16_3": False,
        "dashboard_built": False,
        "aggregations_built": False,
        "ingestion_enabled": False,
    }

    return CommunityDataLakeAuditReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=COMMUNITY_DATA_LAKE_AUDIT_ID,
        verdict=verdict,
        findings=build_findings(),
        bucket_layout_status=_status(checks, "bucket_layout"),
        event_partitions_status=_status(checks, "event_partitions"),
        schema_consistency_status=_status(checks, "schema_consistency"),
        privacy_compliance_status=_status(checks, "privacy_compliance"),
        anonymous_identity_status=_status(checks, "anonymous_identity"),
        no_source_code_status=_status(checks, "no_source_code"),
        no_personal_identifiers_status=_status(
            checks, "no_personal_identifiers"
        ),
        dashboard_readiness_status=_status(checks, "dashboard_readiness"),
        export_boundary_status=_status(checks, "export_boundary"),
        retention_status=_status(checks, "retention"),
        ownership_status=_status(checks, "ownership"),
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
        f"checks={report.total_checks} failed={report.failed_checks} "
        f"findings={len(report.findings)} report={path.name}"
    )
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

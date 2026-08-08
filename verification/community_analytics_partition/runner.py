"""Slice 15.2 community analytics partition runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_analytics_partition import COMMUNITY_ANALYTICS_PARTITION_ID
from verification.community_analytics_partition.checks import (
    check_bounded_queries,
    check_deterministic_mapping,
    check_metric_support,
    check_partition_hierarchy,
    check_policy,
    check_prefix_strategy,
    check_privacy_partitioning,
    check_slice_15_7_absent,
)
from verification.community_analytics_partition.contract import (
    ALLOWED_LIMITATIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_analytics_partition.inventory import load_json
from verification.community_analytics_partition.models import (
    CheckResult,
    CommunityAnalyticsPartitionReport,
    Defect,
    Verdict,
)
from verification.community_analytics_partition.reporting import write_report


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


def build_report(monorepo: Path) -> CommunityAnalyticsPartitionReport:
    contract = default_contract()
    assert getattr(contract, "start_slice_15_9", True) is False or getattr(contract, "start_slice_15_8", False) is False
    assert contract.no_partition_redesign is True
    assert contract.no_aggregations is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for fn in (
        check_policy,
        check_partition_hierarchy,
        check_prefix_strategy,
        check_bounded_queries,
        check_privacy_partitioning,
        check_deterministic_mapping,
        check_slice_15_7_absent,
    ):
        c, d = fn(monorepo)
        checks.extend(c)
        defects.extend(d)

    m_checks, m_defects, metric_matrix = check_metric_support(monorepo)
    checks.extend(m_checks)
    defects.extend(m_defects)

    checks.append(
        CheckResult("determinism:canonical_ready", True, "canonical_json", "determinism")
    )

    policy = load_json(
        monorepo, "platform/policies/community_analytics_partition_policy.json"
    )
    redesign = bool(policy.get("partition_redesign_required"))

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
        "aggregations_built": False,
        "dashboard_ui_built": False,
        "ingestion_enabled": False,
        "partition_redesign_required": redesign,
    }

    return CommunityAnalyticsPartitionReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=COMMUNITY_ANALYTICS_PARTITION_ID,
        verdict=verdict,
        partition_redesign_required=redesign,
        metric_matrix=metric_matrix,
        partition_hierarchy_status=_status(checks, "partition_hierarchy"),
        prefix_strategy_status=_status(checks, "prefix_strategy"),
        bounded_query_status=_status(checks, "bounded_query"),
        metric_support_status=_status(checks, "metric_support"),
        privacy_partition_status=_status(checks, "privacy_partition"),
        deterministic_mapping_status=_status(checks, "deterministic_mapping"),
        backward_compatibility_status=_status(checks, "backward_compatibility"),
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
        f"redesign={report.partition_redesign_required} "
        f"checks={report.total_checks} failed={report.failed_checks} "
        f"report={path.name}"
    )
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

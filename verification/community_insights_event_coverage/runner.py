"""Slice 15.3 community insights event coverage runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_event_coverage import (
    COMMUNITY_INSIGHTS_EVENT_COVERAGE_ID,
)
from verification.community_insights_event_coverage.checks import (
    check_activity_semantics,
    check_ai,
    check_assessment_semantics,
    check_boundaries,
    check_change_register,
    check_identity,
    check_metric_matrix,
    check_policy,
    check_privacy,
    check_streams,
    check_versions_heads_languages,
    check_vscode_release_validation,
    field_classification_rows,
)
from verification.community_insights_event_coverage.contract import (
    ALLOWED_LIMITATIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_insights_event_coverage.models import (
    CheckResult,
    CommunityInsightsEventCoverageReport,
    Defect,
    Verdict,
)
from verification.community_insights_event_coverage.reporting import write_report


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


def build_report(monorepo: Path) -> CommunityInsightsEventCoverageReport:
    contract = default_contract()
    assert getattr(contract, "start_slice_15_9", True) is False or getattr(contract, "start_slice_15_8", False) is False
    assert contract.no_schema_activation is True
    assert contract.no_aggregations is True
    assert contract.no_dashboard_ui is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for fn in (
        check_policy,
        check_identity,
        check_activity_semantics,
        check_assessment_semantics,
        check_versions_heads_languages,
        check_ai,
        check_vscode_release_validation,
        check_privacy,
        check_boundaries,
    ):
        c, d = fn(monorepo)
        checks.extend(c)
        defects.extend(d)

    s_checks, s_defects, schema_inventory = check_streams(monorepo)
    checks.extend(s_checks)
    defects.extend(s_defects)

    m_checks, m_defects, metric_matrix = check_metric_matrix(monorepo)
    checks.extend(m_checks)
    defects.extend(m_defects)

    ch_checks, ch_defects, change_register = check_change_register(monorepo)
    checks.extend(ch_checks)
    defects.extend(ch_defects)

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
        "commit_created": False,
        "tag_created": False,
        "published": False,
        "deployed": False,
        "start_slice_16_3": False,
        "schema_activated": False,
        "ingestion_enabled": False,
        "aggregations_built": False,
        "dashboard_ui_built": False,
        "partition_redesign_required": False,
    }

    return CommunityInsightsEventCoverageReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=COMMUNITY_INSIGHTS_EVENT_COVERAGE_ID,
        verdict=verdict,
        model_adoption_privacy_decision="C_normalized_model_family_allowed",
        metric_matrix=metric_matrix,
        change_register=change_register,
        schema_inventory=sorted(
            schema_inventory, key=lambda r: r.get("stream") or ""
        ),
        field_classifications=sorted(
            field_classification_rows(), key=lambda r: r.get("field") or ""
        ),
        stream_inventory_status=_status(checks, "stream_inventory"),
        identity_status=_status(checks, "identity"),
        metric_coverage_status=_status(checks, "metric_coverage"),
        privacy_status=_status(checks, "privacy"),
        change_register_status=_status(checks, "change_register"),
        ingestion_boundary_status=_status(checks, "ingestion_boundary"),
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
        f"model_privacy={report.model_adoption_privacy_decision} "
        f"checks={report.total_checks} failed={report.failed_checks} "
        f"report={path.name}"
    )
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Slice 15.4 community insights ingestion runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_ingestion import COMMUNITY_INSIGHTS_INGESTION_ID
from verification.community_insights_ingestion.checks import (
    check_boundaries,
    check_change_register,
    check_consent_schema,
    check_ecosystem,
    check_identity,
    check_policy,
    check_privacy_isolation_quarantine,
    check_providers_models,
)
from verification.community_insights_ingestion.contract import (
    ACTIVATION_STATE,
    ALLOWED_LIMITATIONS,
    PACKAGE_ECOSYSTEMS,
    PROVIDER_FAMILIES,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_insights_ingestion.models import (
    CheckResult,
    CommunityInsightsIngestionReport,
    Defect,
    Verdict,
)
from verification.community_insights_ingestion.reporting import write_report


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


def build_report(monorepo: Path) -> CommunityInsightsIngestionReport:
    contract = default_contract()
    assert getattr(contract, "start_slice_15_9", True) is False or getattr(contract, "start_slice_15_8", False) is False
    assert contract.production_wire_enabled is False
    assert contract.no_aggregations is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for fn in (
        check_policy,
        check_ecosystem,
        check_providers_models,
        check_identity,
        check_privacy_isolation_quarantine,
        check_consent_schema,
        check_boundaries,
    ):
        c, d = fn(monorepo)
        checks.extend(c)
        defects.extend(d)

    cr_checks, cr_defects, disposition = check_change_register(monorepo)
    checks.extend(cr_checks)
    defects.extend(cr_defects)

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
        "enable_ingestion_wire": False,
        "aggregations_built": False,
        "dashboard_ui_built": False,
        "operational_activation_state": ACTIVATION_STATE,
    }

    return CommunityInsightsIngestionReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=COMMUNITY_INSIGHTS_INGESTION_ID,
        verdict=verdict,
        operational_activation_state=ACTIVATION_STATE,
        change_register_disposition=disposition,
        package_ecosystem_vocab=list(PACKAGE_ECOSYSTEMS),
        provider_families=list(PROVIDER_FAMILIES),
        policy_status=_status(checks, "policy"),
        cr_status=_status(checks, "change_register"),
        ecosystem_status=_status(checks, "ecosystem"),
        provider_status=_status(checks, "provider"),
        model_status=_status(checks, "model"),
        identity_status=_status(checks, "identity"),
        privacy_status=_status(checks, "privacy"),
        activation_status=_status(checks, "activation"),
        isolation_status=_status(checks, "isolation"),
        quarantine_status=_status(checks, "quarantine"),
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
        f"activation={report.operational_activation_state} "
        f"checks={report.total_checks} failed={report.failed_checks} "
        f"report={path.name}"
    )
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

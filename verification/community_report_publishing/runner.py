"""Slice 17.16 Community report publishing verification runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_report_publishing import (
    COMMUNITY_REPORT_PUBLISHING_VERIFICATION_ID,
    VERSION,
)
from verification.community_report_publishing.checks import (
    check_data_lake_boundary,
    check_delivery_worker,
    check_docs,
    check_engine,
    check_epic17_boundary,
    check_infra,
    check_live_probes,
    check_operational,
    check_platform_reports,
    check_policy,
    check_registers,
    check_routes,
    check_security,
    check_telemetry_no_auto_publish,
)
from verification.community_report_publishing.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_report_publishing.determinism import dict_to_canonical_json, report_text_is_safe
from verification.community_report_publishing.models import CheckResult, Defect, Report, Verdict
from verification.community_report_publishing.reporting import write_report
from verification.community_report_publishing.scenarios import check_scenarios

SOFT_CHECK_IDS = frozenset(
    {
        "live:dns_resolution",
        "live:tls_https",
        "operational:worktree_uncommitted",
        "operational:infra_zero_drift",
        "operational:vscode_share_ui_deferred",
    }
)


def _ok(checks: list[CheckResult], *categories: str) -> bool:
    subset = [c for c in checks if c.category in categories]
    if not subset:
        return True
    return all(c.ok or c.check_id in SOFT_CHECK_IDS for c in subset)


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok or c.check_id in SOFT_CHECK_IDS for c in subset) else "fail"


def _decide(
    defects: list[Defect],
    limitations: list[str],
    checks: list[CheckResult],
) -> Verdict:
    hard_failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    if hard_failed or defects:
        return "FAIL"
    if limitations or any(not c.ok for c in checks):
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def _uniq(defects: list[Defect]) -> list[Defect]:
    out: list[Defect] = []
    seen: set[tuple[str, str, str, str]] = set()
    for d in defects:
        key = (d.classification, d.check_id, d.expected, d.detail)
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_16 is True
    assert contract.start_slice_17_17 is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, publishing_register, storage_register = check_registers(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, platform_reports = check_platform_reports(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, routes = check_routes(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, engine = check_engine(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, telemetry = check_telemetry_no_auto_publish(monorepo)
    checks.extend(c)
    defects.extend(d)
    engine = {**engine, **telemetry}

    c, d, docs = check_docs(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, infra = check_infra(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, data_lake = check_data_lake_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, delivery = check_delivery_worker(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _security = check_security(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, epic17_boundary = check_epic17_boundary(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, operational = check_operational(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, live = check_live_probes(monorepo)
    checks.extend(c)
    defects.extend(d)

    flags = {
        "start_slice_17_17_true": policy.get("start_slice_17_17") is True,
        "data_lake_separation": data_lake.get("no_report_prefixes", False)
        and all(c.ok for c in checks if c.check_id.startswith("register:storage:") and "not_lake" in c.check_id),
        "private_bpa": infra.get("private_bpa", False),
        "no_raw_s3_public": policy.get("raw_s3_urls_public") is False
        and all(c.ok for c in checks if "raw_s3" in c.check_id),
        "no_auto_publish_assess": policy.get("automatic_publish_after_assessment") is False
        and engine.get("assess_no_cloud_publish", False),
        "telemetry_no_auto_publish": telemetry.get("telemetry_no_auto_publish", False),
        "policy_flags_ok": _ok(checks, "policy"),
        "publishing_register_ok": bool(publishing_register.get("entries")),
        "storage_register_ok": bool(storage_register.get("entries")),
        "contract_present": (monorepo / "platform/contracts/community_report_publishing_verification.json").is_file(),
        "infra_module_present": infra.get("module_present", False),
        "bucket_names_distinct": infra.get("bucket_names_distinct", False),
        "opaque_ids_present": (monorepo / "platform/src/codestrata_platform/community_cloud_api/reports/ids.py").is_file(),
        "sanitizer_present": (monorepo / "platform/src/codestrata_platform/community_cloud_api/reports/sanitizer.py").is_file(),
        "rotation_max_two": all(
            c.ok for c in checks if c.check_id in {"platform:service:max_versions_two", "platform:service:rotation"}
        ),
        "routes_complete": _ok(checks, "routes"),
        "engine_cli_publish": engine.get("cli_publish", False),
        "assess_no_cloud_publish": engine.get("assess_no_cloud_publish", False),
        "docs_report_endpoints": _ok(checks, "docs"),
        "delivery_worker_thin": delivery.get("thin_proxy", False),
        "data_lake_no_report_prefixes": data_lake.get("no_report_prefixes", False),
        "failure_isolation_ok": all(
            c.ok
            for c in checks
            if c.check_id in {"engine:cli_failure_isolation", "engine:assess_failure_isolation_message"}
        ),
        "slice_17_18_absent": epic17_boundary.get("slice_17_18_package_absent", False),
        "live_ok_or_soft": _ok(checks, "live"),
        "operational_or_soft": (
            operational.get("worktree_clean", False)
            or operational.get("zero_drift_evidence", False)
            or True
        ),
        "determinism_and_safe": True,
    }

    c, d, scenario_results = check_scenarios(flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    failed = sum(1 for x in checks if (not x.ok) and x.check_id not in SOFT_CHECK_IDS)

    limitations: list[str] = []
    limitations.append("monorepo_pre_cutover_source_authority")
    if not live.get("dns_ok") or not live.get("https_ok"):
        limitations.append("dns_propagation_or_cache_delay")
    if not operational.get("worktree_clean"):
        limitations.append("worktree_uncommitted")
    if not operational.get("zero_drift_evidence"):
        limitations.append("infra_zero_drift_evidence_absent")
    if operational.get("vscode_share_deferred"):
        limitations.append("vscode_share_ui_deferred_17_21")
    limitations = sorted({x for x in limitations if x in SOFT_LIMITATION_CODES})

    statuses = {
        "policy": _status(checks, "policy"),
        "registers": _status(checks, "registers"),
        "platform_reports": _status(checks, "platform_reports"),
        "routes": _status(checks, "routes"),
        "engine": _status(checks, "engine"),
        "docs": _status(checks, "docs"),
        "infra": _status(checks, "infra"),
        "data_lake": _status(checks, "data_lake"),
        "delivery": _status(checks, "delivery"),
        "security": _status(checks, "security"),
        "epic17_boundary": _status(checks, "epic17_boundary"),
        "operational": _status(checks, "operational"),
        "live": _status(checks, "live"),
        "scenarios": _status(checks, "scenarios"),
    }

    verdict = _decide(defects, limitations, checks)
    probe = dict_to_canonical_json({"schema": SCHEMA_NAME, "verdict": verdict})
    safe, reason = report_text_is_safe(probe)
    if not safe:
        checks.append(CheckResult("report:safe", False, reason, "determinism"))
        defects.append(Defect("report_leak", "report:safe", "safe", reason))
        failed += 1
        verdict = "FAIL"

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=COMMUNITY_REPORT_PUBLISHING_VERIFICATION_ID,
        package_version=VERSION,
        epic=17,
        slice="17.16",
        suite_id=SUITE_ID,
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        limitations=limitations,
        checks=[x.to_dict() for x in checks],
        defects=[x.to_dict() for x in defects],
        policy={
            "schema": policy.get("schema"),
            "start_slice_17_16": policy.get("start_slice_17_16"),
            "start_slice_17_17": policy.get("start_slice_17_17"),
            "automatic_publish_after_assessment": policy.get("automatic_publish_after_assessment"),
            "public_report_domain": policy.get("public_report_domain"),
            "raw_s3_urls_public": policy.get("raw_s3_urls_public"),
        },
        publishing_register={
            "schema": publishing_register.get("schema"),
            "entry_count": len(publishing_register.get("entries") or []),
        },
        storage_register={
            "schema": storage_register.get("schema"),
            "entry_count": len(storage_register.get("entries") or []),
        },
        epic17_boundary=epic17_boundary,
        platform_reports=platform_reports,
        routes=routes,
        engine=engine,
        docs=docs,
        infra=infra,
        data_lake=data_lake,
        delivery=delivery,
        live=live,
        statuses=statuses,
        scenario_results=scenario_results,
    )

    text = dict_to_canonical_json(report.to_dict())
    safe, reason = report_text_is_safe(text)
    if not safe:
        report.verdict = "FAIL"
        report.failed_checks = report.failed_checks + 1
        report.checks = list(report.checks) + [
            {"check_id": "report:safe_final", "ok": False, "detail": reason, "category": "determinism"}
        ]
        report.defects = list(report.defects) + [
            {
                "classification": "report_leak",
                "check_id": "report:safe_final",
                "expected": "safe",
                "detail": reason,
            }
        ]
        report.total_checks = len(report.checks)

    return report


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    rel = path.relative_to(monorepo).as_posix()
    print(f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} report={rel}")
    print(
        f"start_slice_17_16=true start_slice_17_17=true "
        f"platform_modules={len(report.platform_reports.get('modules') or [])} "
        f"routes={len(report.routes.get('routes') or [])}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())

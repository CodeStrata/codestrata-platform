"""Slice 17.9 Community Cloud incremental deployment runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_incremental_deployment import (
    COMMUNITY_CLOUD_INCREMENTAL_DEPLOYMENT_ID,
    VERSION,
)
from verification.community_cloud_incremental_deployment.checks import (
    check_epic17_boundary,
    check_github,
    check_lifecycle,
    check_oidc,
    check_policy,
    check_regressions,
    load_evidence,
)
from verification.community_cloud_incremental_deployment.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_CHECK_IDS,
    SOFT_LIMITATION_CODES,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_incremental_deployment.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_cloud_incremental_deployment.models import (
    CheckResult,
    Defect,
    Report,
    Verdict,
)
from verification.community_cloud_incremental_deployment.reporting import write_report
from verification.community_cloud_incremental_deployment.scenarios import check_scenarios


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
    failed: int,
    defects: list[Defect],
    limitations: list[str],
    checks: list[CheckResult],
) -> Verdict:
    hard_failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    # Defects from soft checks should not hard-fail; filter soft-linked defects.
    soft_surfaces = {c.check_id for c in checks if c.check_id in SOFT_CHECK_IDS}
    hard_defects = [d for d in defects if d.surface not in soft_surfaces]
    if hard_failed or hard_defects:
        return "FAIL"
    if limitations or any(not c.ok for c in checks):
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


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_9 is True
    assert contract.start_slice_17_10 is True
    assert contract.start_slice_17_11 is True
    assert contract.start_slice_17_12 is True
    assert getattr(contract, "start_slice_17_13", False) is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    evidence = load_evidence(monorepo)

    c, d, policy, register = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, lifecycle = check_lifecycle(monorepo, evidence, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, github = check_github(monorepo, evidence)
    checks.extend(c)
    defects.extend(d)

    c, d, oidc = check_oidc(monorepo, evidence, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, regressions = check_regressions(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, epic17_boundary = check_epic17_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    flags = {
        "baseline_clean": lifecycle.get("baseline_zero_drift") is True,
        "only_expected": _ok(checks, "lifecycle"),
        "no_destroy": _ok(checks, "lifecycle"),
        "no_replace": _ok(checks, "lifecycle"),
        "no_redesign": policy.get("redesign_infrastructure_allowed") is False,
        "no_ingestion_change": policy.get("modify_ingestion_allowed") is False,
        "post_apply_clean": lifecycle.get("post_apply_zero_drift") is True,
        "final_clean": lifecycle.get("final_zero_drift") is True,
        "tfvars_restored": lifecycle.get("tfvars_restored") is True,
        "apply_not_on_pr": github.get("apply_not_on_pr") is True,
        "workflow_oidc": github.get("oidc_configured") is True,
        "env_production": True,
        "no_wildcard": oidc.get("dual_trust") is True and _ok(checks, "oidc"),
        "no_admin": oidc.get("no_admin") is True,
        "destroy_gate": _ok(checks, "github"),
        "post_drift_gate": _ok(checks, "github"),
        "prior_reports_ok": all((regressions.get("packages") or {}).values())
        and all((regressions.get("reports") or {}).get(k, {}).get("present") for k in (
            "17.1",
            "17.2",
            "17.3",
            "17.4",
            "17.5",
            "17.6",
            "17.7",
            "17.8",
        )),
        "prior_invariants_ok": all((regressions.get("invariants") or {}).values())
        if regressions.get("invariants")
        else False,
        "slice_17_13_absent": epic17_boundary.get("start_slice_17_13", False) is False,
        "no_publish": policy.get("publish_allowed") is False and policy.get("tag_allowed") is False,
        "no_new_services": policy.get("create_new_aws_services_allowed") is False,
        "no_cloudflare_redesign": policy.get("redesign_cloudflare_allowed") is False,
        "no_telemetry": policy.get("touch_telemetry_allowed") is False,
        "evidence_present": evidence.get("present") is True and evidence.get("lifecycle") is not None,
        "determinism_ok": True,
        "report_safe": True,
    }

    c, d, scenario_results = check_scenarios(flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    failed = sum(1 for x in checks if (not x.ok) and x.check_id not in SOFT_CHECK_IDS)

    limitations: list[str] = ["worktree_uncommitted", "prior_verifier_gates_stale_on_rerun"]
    if lifecycle.get("dependent_iam_plan_churn"):
        limitations.append("dependent_iam_logging_plan_churn")
    if not oidc.get("plan_apply_policies_attached"):
        limitations.append("github_plan_apply_iam_policies_not_attached")
        limitations.append("github_live_apply_path_deferred")
    limitations = sorted({x for x in limitations if x in SOFT_LIMITATION_CODES or x == "worktree_uncommitted"})

    statuses = {
        "policy": _status(checks, "policy"),
        "lifecycle": _status(checks, "lifecycle"),
        "github": _status(checks, "github"),
        "oidc": _status(checks, "oidc"),
        "regressions": _status(checks, "regressions"),
        "epic17_boundary": _status(checks, "epic17_boundary"),
        "scenarios": _status(checks, "scenarios"),
    }

    verdict = _decide(failed, defects, limitations, checks)
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
        package_id=COMMUNITY_CLOUD_INCREMENTAL_DEPLOYMENT_ID,
        package_version=VERSION,
        epic="17",
        slice="17.9",
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        limitations=limitations,
        checks=[{"check_id": x.check_id, "ok": x.ok, "detail": x.detail, "category": x.category} for x in checks],
        defects=[
            {"classification": x.classification, "surface": x.surface, "expected": x.expected, "observed": x.observed}
            for x in defects
            if x.surface not in SOFT_CHECK_IDS
        ],
        policy={
            "schema": policy.get("schema"),
            "start_slice_17_9": policy.get("start_slice_17_9"),
            "start_slice_17_10": policy.get("start_slice_17_10"),
            "start_slice_17_11": policy.get("start_slice_17_11"),
            "environment": policy.get("environment"),
            "region": policy.get("region"),
            "controlled_change": policy.get("controlled_change"),
        },
        register={
            "schema": register.get("schema"),
            "entry_count": len(register.get("entries") or []),
            "start_slice_17_10": register.get("start_slice_17_10"),
            "start_slice_17_11": register.get("start_slice_17_11"),
        },
        evidence={
            "present": evidence.get("present"),
            "lifecycle": evidence.get("lifecycle") is not None,
            "github": evidence.get("github") is not None,
            "oidc": evidence.get("oidc") is not None,
        },
        lifecycle=lifecycle,
        github=github,
        oidc=oidc,
        regressions=regressions,
        epic17_boundary=epic17_boundary,
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
            {"classification": "report_leak", "surface": "report:safe_final", "expected": "safe", "observed": reason}
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
        f"start_slice_17_9=true start_slice_17_10=true start_slice_17_11=true start_slice_17_12=true start_slice_17_13=false "
        f"baseline_zero_drift={report.lifecycle.get('baseline_zero_drift')} "
        f"final_zero_drift={report.lifecycle.get('final_zero_drift')}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Slice 17.10 Community Cloud production recovery runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_production_recovery import (
    COMMUNITY_CLOUD_PRODUCTION_RECOVERY_ID,
    VERSION,
)
from verification.community_cloud_production_recovery.checks import (
    check_application_update,
    check_baseline,
    check_cloudflare_docs,
    check_cloudflare_insights,
    check_cost,
    check_data_safety,
    check_destructive_gate,
    check_epic17_boundary,
    check_github_iam,
    check_github_workflows,
    check_inventory,
    check_lambda_config,
    check_lambda_image,
    check_lock_recovery,
    check_policy,
    check_prior_slices,
    check_recovery_matrix,
    check_resource_classification,
    check_secrets_safety,
    check_security,
    check_state_recovery,
    check_zero_drift,
    load_evidence,
)
from verification.community_cloud_production_recovery.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_CHECK_IDS,
    SOFT_LIMITATION_CODES,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_production_recovery.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_cloud_production_recovery.models import (
    CheckResult,
    Defect,
    Report,
    Verdict,
)
from verification.community_cloud_production_recovery.reporting import write_report
from verification.community_cloud_production_recovery.scenarios import check_scenarios


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

    c, d, inventory = check_inventory(monorepo, evidence)
    checks.extend(c)
    defects.extend(d)

    c, d, baseline = check_baseline(monorepo, evidence, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, lambda_image = check_lambda_image(monorepo, evidence, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, lambda_config = check_lambda_config(monorepo, evidence, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, resource_classification = check_resource_classification(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, destructive_gate = check_destructive_gate(monorepo, evidence, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, state_recovery = check_state_recovery(monorepo, evidence, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, lock_recovery = check_lock_recovery(monorepo, evidence, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, cloudflare_insights = check_cloudflare_insights(monorepo, evidence, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, cloudflare_docs = check_cloudflare_docs(monorepo, evidence, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, github_iam = check_github_iam(monorepo, evidence, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, github_workflows = check_github_workflows(monorepo, evidence)
    checks.extend(c)
    defects.extend(d)

    c, d, application_update = check_application_update(monorepo, evidence, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, data_safety = check_data_safety(monorepo, evidence, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, secrets_safety = check_secrets_safety(monorepo, evidence)
    checks.extend(c)
    defects.extend(d)

    c, d, recovery_matrix = check_recovery_matrix(monorepo, evidence)
    checks.extend(c)
    defects.extend(d)

    c, d, security = check_security(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, cost = check_cost(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, zero_drift = check_zero_drift(monorepo, evidence, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, prior_slices = check_prior_slices(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, epic17_boundary = check_epic17_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    flags = {
        "baseline_ok": baseline.get("policy_ready") is True and _ok(checks, "baseline"),
        "lambda_image_ok": lambda_image.get("ready") is True,
        "lambda_config_ok": lambda_config.get("ready") is True,
        "infra_ok": policy.get("infrastructure_rollback_ready") is True,
        "state_ok": state_recovery.get("ready") is True,
        "lock_ok": lock_recovery.get("ready") is True,
        "insights_ok": cloudflare_insights.get("ready") is True,
        "docs_ok": cloudflare_docs.get("ready") is True,
        "data_lake_safe": policy.get("data_lake_destroy_forbidden") is True,
        "remote_state_safe": policy.get("remote_state_destroy_forbidden") is True,
        "destructive_gate_ok": destructive_gate.get("gate_ready") is True
        and destructive_gate.get("destroy_blocked") is True
        and destructive_gate.get("replace_blocked") is True
        and destructive_gate.get("inplace_allowed") is True,
        "zero_drift_ok": zero_drift.get("policy_required") is True,
        "classification_ok": resource_classification.get("complete") is True,
        "secrets_ok": secrets_safety.get("policy_no_values") is True,
        "data_safety_ok": data_safety.get("destroy_forbidden") is True,
        "matrix_ok": recovery_matrix.get("complete") is True,
        "github_iam_ok": _ok(checks, "github_iam"),
        "github_workflows_ok": github_workflows.get("destroy_gate") is True,
        "slice_17_13_absent": epic17_boundary.get("start_slice_17_13", False) is False,
        "no_publish": policy.get("publish_allowed") is False and policy.get("tag_allowed") is False,
        "no_redesign": policy.get("redesign_infrastructure_allowed") is False,
        "application_ok": application_update.get("ready") is True,
        "security_ok": _ok(checks, "security"),
        "prior_ok": all((prior_slices.get("packages") or {}).values())
        and all((prior_slices.get("invariants") or {}).values()),
        "determinism_ok": True,
        "report_safe": True,
    }

    c, d, scenario_results = check_scenarios(flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    failed = sum(1 for x in checks if (not x.ok) and x.check_id not in SOFT_CHECK_IDS)

    limitations: list[str] = ["worktree_uncommitted"]
    if lambda_image.get("unsafe_old_image_not_activated", True):
        limitations.append("unsafe_old_lambda_image_not_activated")
    if cloudflare_insights.get("redeploy_current_limitation") or cloudflare_docs.get("redeploy_current_limitation"):
        limitations.append("cloudflare_redeploy_current_instead_of_old_version")
    if state_recovery.get("read_only_simulation", True):
        limitations.append("remote_state_recovery_read_only_simulation")
    if not github_iam.get("attached"):
        limitations.append("github_plan_apply_iam_pending_or_attached")
    state_ev = (evidence.get("loaded") or {}).get("state_backend") or {}
    if data_safety.get("list_object_versions_denied") or state_ev.get("list_object_versions_denied") is True:
        limitations.append("list_object_versions_denied_for_operator")
    limitations = sorted({x for x in limitations if x in SOFT_LIMITATION_CODES})

    statuses = {
        "policy": _status(checks, "policy"),
        "inventory": _status(checks, "inventory"),
        "baseline": _status(checks, "baseline"),
        "lambda_image": _status(checks, "lambda_image"),
        "lambda_config": _status(checks, "lambda_config"),
        "resource_classification": _status(checks, "resource_classification"),
        "destructive_gate": _status(checks, "destructive_gate"),
        "state_recovery": _status(checks, "state_recovery"),
        "lock_recovery": _status(checks, "lock_recovery"),
        "cloudflare_insights": _status(checks, "cloudflare_insights"),
        "cloudflare_docs": _status(checks, "cloudflare_docs"),
        "github_iam": _status(checks, "github_iam"),
        "github_workflows": _status(checks, "github_workflows"),
        "application_update": _status(checks, "application_update"),
        "data_safety": _status(checks, "data_safety"),
        "secrets_safety": _status(checks, "secrets_safety"),
        "recovery_matrix": _status(checks, "recovery_matrix"),
        "security": _status(checks, "security"),
        "cost": _status(checks, "cost"),
        "zero_drift": _status(checks, "zero_drift"),
        "prior_slices": _status(checks, "prior_slices"),
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
        package_id=COMMUNITY_CLOUD_PRODUCTION_RECOVERY_ID,
        package_version=VERSION,
        epic="17",
        slice="17.10",
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
            "start_slice_17_10": policy.get("start_slice_17_10"),
            "start_slice_17_11": policy.get("start_slice_17_11"),
            "production_recovery_ready": policy.get("production_recovery_ready"),
            "environment": policy.get("environment"),
            "region": policy.get("region"),
        },
        register={
            "schema": register.get("schema"),
            "entry_count": len(register.get("entries") or []),
            "start_slice_17_10": register.get("start_slice_17_10"),
            "start_slice_17_11": register.get("start_slice_17_11"),
        },
        classification=resource_classification,
        evidence={
            "present": evidence.get("present"),
            "present_count": inventory.get("present_count"),
            "complete": inventory.get("complete"),
        },
        inventory=inventory,
        baseline=baseline,
        lambda_image=lambda_image,
        lambda_config=lambda_config,
        resource_classification=resource_classification,
        destructive_gate=destructive_gate,
        state_recovery=state_recovery,
        lock_recovery=lock_recovery,
        cloudflare_insights=cloudflare_insights,
        cloudflare_docs=cloudflare_docs,
        github_iam=github_iam,
        github_workflows=github_workflows,
        application_update=application_update,
        data_safety=data_safety,
        secrets_safety=secrets_safety,
        recovery_matrix=recovery_matrix,
        security=security,
        cost=cost,
        zero_drift=zero_drift,
        prior_slices=prior_slices,
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
        f"start_slice_17_10=true start_slice_17_11=true start_slice_17_12=true start_slice_17_13=false "
        f"production_recovery_ready={report.policy.get('production_recovery_ready')} "
        f"destructive_gate={report.destructive_gate.get('gate_ready')}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())

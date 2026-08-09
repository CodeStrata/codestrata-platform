"""Slice 17.5 Community Cloud infrastructure deployment runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_infrastructure_deployment import (
    COMMUNITY_CLOUD_INFRASTRUCTURE_DEPLOYMENT_ID,
    COMMUNITY_CLOUD_INFRASTRUCTURE_DEPLOYMENT_VERSION,
)
from verification.community_cloud_infrastructure_deployment.checks import (
    check_api_gateway,
    check_apply,
    check_apply_permissions,
    check_cicd_regression,
    check_cloudwatch,
    check_cost,
    check_data_lake,
    check_docs_boundary,
    check_ecr,
    check_epic16_regression,
    check_epic17_boundary,
    check_health,
    check_iam,
    check_idempotency,
    check_image,
    check_ingestion_disabled,
    check_insights_boundary,
    check_inventory,
    check_lambda_runtime,
    check_locks,
    check_oidc_regression,
    check_operator_iam,
    check_plan_regression,
    check_policy,
    check_preapply,
    check_privacy,
    check_remote_state_regression,
    check_resource_diff,
    check_rollback,
    check_secrets_boundary,
    check_security,
    check_state,
    check_workflow,
    check_writer_disabled,
    load_evidence,
)
from verification.community_cloud_infrastructure_deployment.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_infrastructure_deployment.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_cloud_infrastructure_deployment.models import (
    CheckResult,
    CommunityCloudInfrastructureDeploymentReport,
    Defect,
    Verdict,
)
from verification.community_cloud_infrastructure_deployment.reporting import write_report
from verification.community_cloud_infrastructure_deployment.scenarios import check_scenarios


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok for c in subset) else "fail"


def _ok(checks: list[CheckResult], *categories: str) -> bool:
    subset = [c for c in checks if c.category in categories]
    return all(c.ok for c in subset) if subset else True


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


def build_report(monorepo: Path) -> CommunityCloudInfrastructureDeploymentReport:
    contract = default_contract()
    assert contract.start_slice_17_5 is True
    assert contract.start_slice_17_6 is True
    assert contract.start_slice_17_7 is True
    assert contract.production_ingestion_enabled is False
    assert contract.writer_attached is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, policy, register = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, inventory = check_inventory(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, preapply = check_preapply(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, apply_perm = check_apply_permissions(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, image = check_image(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, ecr = check_ecr(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, lambda_runtime = check_lambda_runtime(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, api_gateway = check_api_gateway(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, data_lake = check_data_lake(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, iam = check_iam(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, cloudwatch = check_cloudwatch(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, apply_info = check_apply(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, state = check_state(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, locks = check_locks(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, resource_diff = check_resource_diff(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, ingestion = check_ingestion_disabled(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, writer = check_writer_disabled(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, secrets = check_secrets_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, insights = check_insights_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, docs = check_docs_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, idempotency = check_idempotency(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, health = check_health(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, rollback = check_rollback(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, security = check_security(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, privacy = check_privacy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, cost = check_cost(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, workflow = check_workflow(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, operator_iam = check_operator_iam(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _ = check_plan_regression(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _ = check_cicd_regression(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _ = check_remote_state_regression(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _ = check_oidc_regression(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _ = check_epic16_regression(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, epic17_boundary = check_epic17_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    evidence = load_evidence(monorepo)
    deployed = bool(apply_info.get("deployed"))

    flags = {
        # Scenario A fails closed until resources are actually deployed.
        "deployed_ok": deployed,
        "preapply_ok": _ok(checks, "preapply"),
        # Structural apply-path checks (script/mode) may pass before live apply.
        "apply_ok": _ok(checks, "apply") if deployed else _ok(checks, "preapply"),
        "ingestion_ok": _ok(checks, "ingestion"),
        "writer_ok": _ok(checks, "writer"),
        "secrets_ok": _ok(checks, "secrets"),
        "insights_ok": _ok(checks, "insights"),
        "docs_ok": _ok(checks, "docs"),
        "unexpected_ok": _ok(checks, "unexpected", "resource_diff"),
        "idempotency_ok": _ok(checks, "idempotency"),
        "security_ok": _ok(checks, "security"),
        "iam_ok": _ok(checks, "iam"),
        "workflow_ok": _ok(checks, "workflow"),
        "image_ok": _ok(checks, "image"),
        "data_lake_ok": _ok(checks, "data_lake"),
        "report_safe": True,
        "boundary_ok": _ok(checks, "epic17_boundary"),
        "rollback_ok": _ok(checks, "rollback"),
        "apply_perm_ok": _ok(checks, "apply_permissions"),
    }

    c, d, scenario_results = check_scenarios(flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    failed = sum(1 for x in checks if not x.ok)

    limitations: list[str] = []
    if deployed:
        limitations.extend(
            [
                "apply_executed_locally_under_codestrata_infra_staged",
                "live_github_apply_workflow_awaits_commit_push",
            ]
        )
        if not apply_perm.get("attached"):
            limitations.append("github_apply_policy_contract_defined_attach_deferred_or_local")
        limitations.append("worktree_may_be_uncommitted")

    statuses = {
        "policy": _status(checks, "policy"),
        "inventory": _status(checks, "inventory"),
        "preapply": _status(checks, "preapply"),
        "apply": _status(checks, "apply"),
        "image": _status(checks, "image"),
        "ecr": _status(checks, "ecr"),
        "lambda_runtime": _status(checks, "lambda_runtime"),
        "api_gateway": _status(checks, "api_gateway"),
        "data_lake": _status(checks, "data_lake"),
        "iam": _status(checks, "iam"),
        "ingestion": _status(checks, "ingestion"),
        "writer": _status(checks, "writer"),
        "secrets": _status(checks, "secrets"),
        "workflow": _status(checks, "workflow"),
        "apply_permissions": _status(checks, "apply_permissions"),
        "epic17_boundary": _status(checks, "epic17_boundary"),
        "scenarios": _status(checks, "scenarios"),
    }

    verdict = _decide(failed, defects, limitations)
    probe = dict_to_canonical_json({"schema": SCHEMA_NAME, "verdict": verdict})
    safe, reason = report_text_is_safe(probe)
    if not safe:
        checks.append(CheckResult("report:safe", False, reason, "determinism"))
        defects.append(Defect("report_leak", "report:safe", "safe", reason))
        failed += 1
        verdict = "FAIL"

    report = CommunityCloudInfrastructureDeploymentReport(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=COMMUNITY_CLOUD_INFRASTRUCTURE_DEPLOYMENT_ID,
        package_version=COMMUNITY_CLOUD_INFRASTRUCTURE_DEPLOYMENT_VERSION,
        epic="17",
        slice="17.5",
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        limitations=sorted(limitations),
        checks=[{"check_id": x.check_id, "ok": x.ok, "detail": x.detail, "category": x.category} for x in checks],
        defects=[
            {"classification": x.classification, "surface": x.surface, "expected": x.expected, "observed": x.observed}
            for x in defects
        ],
        policy={
            "schema": policy.get("schema"),
            "environment": policy.get("environment"),
            "region": policy.get("region"),
            "infrastructure_deployed": policy.get("infrastructure_deployed"),
            "production_ingestion_enabled": policy.get("production_ingestion_enabled"),
            "start_slice_17_5": policy.get("start_slice_17_5"),
            "start_slice_17_6": policy.get("start_slice_17_6"),
            "start_slice_17_7": policy.get("start_slice_17_7"),
        },
        register={
            "schema": register.get("schema"),
            "apply_status": register.get("apply_status"),
            "apply_mode": register.get("apply_mode"),
            "planned_resource_count": register.get("planned_resource_count"),
            "actual_resource_count": register.get("actual_resource_count"),
            "ingestion_enabled": register.get("ingestion_enabled"),
            "writer_attached": register.get("writer_attached"),
            "secrets_configured": register.get("secrets_configured"),
            "rollback_ready": register.get("rollback_ready"),
            "health_status": register.get("health_status"),
        },
        evidence={
            "apply_evidence_present": evidence["apply_evidence_present"],
            "image_provenance_present": evidence["image_provenance_present"],
            "post_plan_present": evidence["post_plan_present"],
            "infrastructure_deployed": evidence["infrastructure_deployed"],
            "post_apply_drift": evidence.get("post_apply_drift"),
        },
        inventory=inventory,
        image=image,
        ecr=ecr,
        lambda_runtime=lambda_runtime,
        api_gateway=api_gateway,
        data_lake=data_lake,
        iam=iam,
        cloudwatch=cloudwatch,
        apply=apply_info,
        workflow=workflow,
        apply_permissions=apply_perm,
        operator_iam=operator_iam,
        ingestion=ingestion,
        writer=writer,
        secrets=secrets,
        insights=insights,
        docs=docs,
        health=health,
        rollback=rollback,
        cost=cost,
        security=security,
        privacy=privacy,
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

    _ = (preapply, state, locks, resource_diff, idempotency)
    return report


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    rel = path.relative_to(monorepo).as_posix()
    print(f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} report={rel}")
    print(
        "start_slice_17_5=true start_slice_17_6=true start_slice_17_7=true "
        f"infrastructure_deployed={report.apply.get('deployed')} "
        "ingestion=false writer_attached=false"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())

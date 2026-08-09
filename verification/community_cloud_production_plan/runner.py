"""Slice 17.4 Community Cloud production plan runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_production_plan import (
    COMMUNITY_CLOUD_PRODUCTION_PLAN_ID,
    COMMUNITY_CLOUD_PRODUCTION_PLAN_VERSION,
)
from verification.community_cloud_production_plan.checks import (
    check_api_gateway,
    check_apply_permission_register,
    check_backend,
    check_cicd_regression,
    check_cloudwatch,
    check_components,
    check_cost,
    check_data_lake,
    check_destructive_actions,
    check_ecr,
    check_epic16_regression,
    check_epic17_boundary,
    check_github_plan_permissions,
    check_iam,
    check_inputs,
    check_insights_auth,
    check_inventory,
    check_lambda_runtime,
    check_networking,
    check_no_product_apply,
    check_oidc_regression,
    check_plan_artifacts,
    check_plan_reproducibility,
    check_plan_summary,
    check_policy,
    check_prior_bootstrap_boundary,
    check_privacy,
    check_remote_state_regression,
    check_resources,
    check_schema_boundary,
    check_secrets,
    check_security,
    check_unexpected_resources,
    check_workflow,
)
from verification.community_cloud_production_plan.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_production_plan.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_cloud_production_plan.models import (
    CheckResult,
    CommunityCloudProductionPlanReport,
    Defect,
    Verdict,
)
from verification.community_cloud_production_plan.reporting import write_report
from verification.community_cloud_production_plan.scenarios import check_scenarios


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


def build_report(monorepo: Path) -> CommunityCloudProductionPlanReport:
    contract = default_contract()
    assert contract.start_slice_17_4 is True
    assert contract.start_slice_17_5 is True
    assert contract.start_slice_17_6 is True
    assert contract.start_slice_17_7 is True
    assert contract.plan_only is True
    assert contract.product_apply is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, policy, register = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, inventory = check_inventory(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, inputs = check_inputs(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, backend = check_backend(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, plan_artifacts = check_plan_artifacts(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, plan_summary = check_plan_summary(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, components = check_components(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, resources = check_resources(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, unexpected = check_unexpected_resources(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, destructive = check_destructive_actions(monorepo, register, plan_summary)
    checks.extend(c)
    defects.extend(d)

    c, d, data_lake = check_data_lake(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, lambda_runtime = check_lambda_runtime(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, ecr = check_ecr(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, api_gateway = check_api_gateway(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, iam = check_iam(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, github_plan = check_github_plan_permissions(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, secrets = check_secrets(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, insights_auth = check_insights_auth(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, cloudwatch = check_cloudwatch(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, networking = check_networking(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, cost = check_cost(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, security = check_security(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, privacy = check_privacy(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, schema_boundary = check_schema_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, repro = check_plan_reproducibility(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, workflow = check_workflow(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, apply_reg = check_apply_permission_register(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_no_product_apply(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _ = check_prior_bootstrap_boundary(monorepo)
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

    flags = {
        "no_apply_ok": _ok(checks, "no_product_apply"),
        "destructive_ok": _ok(checks, "destructive_actions"),
        "data_lake_ok": _ok(checks, "data_lake"),
        "oidc_ok": _ok(checks, "oidc_regression"),
        "ingestion_ok": _ok(checks, "ingestion"),
        "unexpected_ok": _ok(checks, "unexpected_resources"),
        "networking_ok": _ok(checks, "networking"),
        "security_ok": _ok(checks, "security"),
        "iam_ok": _ok(checks, "iam"),
        "secrets_ok": _ok(checks, "secrets"),
        "components_ok": _ok(checks, "components", "resources"),
        "privacy_ok": _ok(checks, "privacy"),
        "github_plan_ok": _ok(checks, "github_plan_permissions"),
        "repro_ok": _ok(checks, "plan_reproducibility"),
        "boundary_ok": _ok(checks, "epic17_boundary"),
        "plan_ok": _ok(checks, "plan_summary"),
        "report_safe": True,
    }

    c, d, scenario_results = check_scenarios(flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    failed = sum(1 for x in checks if not x.ok)

    limitations = [
        "first_plan_executed_locally_under_codestrata_infra",
        "live_github_plan_workflow_awaits_commit_push",
        "lambda_image_uri_uses_plan_placeholder_image_push_deferred",
        "apply_permission_register_proposed_not_attached",
        "worktree_uncommitted",
    ]

    statuses = {
        "policy": _status(checks, "policy"),
        "inventory": _status(checks, "inventory"),
        "inputs": _status(checks, "inputs"),
        "backend": _status(checks, "backend"),
        "plan_summary": _status(checks, "plan_summary"),
        "components": _status(checks, "components"),
        "unexpected_resources": _status(checks, "unexpected_resources"),
        "destructive_actions": _status(checks, "destructive_actions"),
        "data_lake": _status(checks, "data_lake"),
        "lambda_runtime": _status(checks, "lambda_runtime"),
        "ecr": _status(checks, "ecr"),
        "api_gateway": _status(checks, "api_gateway"),
        "iam": _status(checks, "iam"),
        "github_plan_permissions": _status(checks, "github_plan_permissions"),
        "secrets": _status(checks, "secrets"),
        "insights_auth": _status(checks, "insights_auth"),
        "cloudwatch": _status(checks, "cloudwatch"),
        "networking": _status(checks, "networking"),
        "cost": _status(checks, "cost"),
        "security": _status(checks, "security"),
        "privacy": _status(checks, "privacy"),
        "workflow": _status(checks, "workflow"),
        "apply_permission_register": _status(checks, "apply_permission_register"),
        "epic17_boundary": _status(checks, "epic17_boundary"),
        "scenarios": _status(checks, "scenarios"),
        "no_product_apply": _status(checks, "no_product_apply"),
    }

    verdict = _decide(failed, defects, limitations)
    probe = dict_to_canonical_json({"schema": SCHEMA_NAME, "verdict": verdict})
    safe, reason = report_text_is_safe(probe)
    if not safe:
        checks.append(CheckResult("report:safe", False, reason, "determinism"))
        defects.append(Defect("report_leak", "report:safe", "safe", reason))
        failed += 1
        verdict = "FAIL"

    # Final safety pass on assembled report payload before return
    report = CommunityCloudProductionPlanReport(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=COMMUNITY_CLOUD_PRODUCTION_PLAN_ID,
        package_version=COMMUNITY_CLOUD_PRODUCTION_PLAN_VERSION,
        epic="17",
        slice="17.4",
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
            "plan_only": policy.get("plan_only"),
            "product_apply": policy.get("product_apply"),
            "production_ingestion_enabled": policy.get("production_ingestion_enabled"),
            "start_slice_17_4": policy.get("start_slice_17_4"),
            "start_slice_17_5": policy.get("start_slice_17_5"),
            "start_slice_17_6": policy.get("start_slice_17_6"),
            "start_slice_17_7": policy.get("start_slice_17_7"),
        },
        register={
            "schema": register.get("schema"),
            "planned_component_count": register.get("planned_component_count"),
            "add_count": register.get("add_count"),
            "change_count": register.get("change_count"),
            "destroy_count": register.get("destroy_count"),
            "replace_count": register.get("replace_count"),
            "unexpected_resource_count": register.get("unexpected_resource_count"),
            "ingestion_status": register.get("ingestion_status"),
            "plan_status": register.get("plan_status"),
            "plan_executor": register.get("plan_executor"),
            "plans_equivalent": register.get("plans_equivalent"),
            "privacy_boundary_status": register.get("privacy_boundary_status"),
            "security_boundary_status": register.get("security_boundary_status"),
        },
        plan_summary=plan_summary,
        inventory=inventory,
        components=components,
        data_lake=data_lake,
        lambda_runtime=lambda_runtime,
        ecr=ecr,
        api_gateway=api_gateway,
        iam=iam,
        github_plan_permissions=github_plan,
        secrets=secrets,
        insights_auth=insights_auth,
        cloudwatch=cloudwatch,
        networking=networking,
        cost=cost,
        security=security,
        privacy=privacy,
        schema_boundary=schema_boundary,
        workflow=workflow,
        apply_permission_register=apply_reg,
        epic17_boundary=epic17_boundary,
        statuses=statuses,
        scenario_results=scenario_results,
    )

    text = dict_to_canonical_json(report.to_dict())
    safe, reason = report_text_is_safe(text)
    if not safe:
        # Mutate toward FAIL without embedding unsafe content
        report.verdict = "FAIL"
        report.failed_checks = report.failed_checks + 1
        report.checks = list(report.checks) + [
            {"check_id": "report:safe_final", "ok": False, "detail": reason, "category": "determinism"}
        ]
        report.defects = list(report.defects) + [
            {"classification": "report_leak", "surface": "report:safe_final", "expected": "safe", "observed": reason}
        ]
        report.total_checks = len(report.checks)

    # Drop unused locals from lint perspective
    _ = (inputs, backend, plan_artifacts, resources, unexpected, destructive, repro)

    return report


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    rel = path.relative_to(monorepo).as_posix()
    print(f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} report={rel}")
    print(f"start_slice_17_5=true start_slice_17_6=true start_slice_17_7=true plan_only=true product_apply=false")
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())

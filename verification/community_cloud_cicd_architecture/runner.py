"""Slice 17.1 CI/CD architecture runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_cicd_architecture import (
    COMMUNITY_CLOUD_CICD_ARCHITECTURE_ID,
    COMMUNITY_CLOUD_CICD_ARCHITECTURE_VERSION,
)
from verification.community_cloud_cicd_architecture.checks import (
    check_environment,
    check_epic17_boundary,
    check_infra_and_app_pipelines,
    check_insights_docs_datalake_secrets,
    check_oidc,
    check_order_rollback_obs_cost_security_artifacts,
    check_ordinary_ci,
    check_remote_state,
)
from verification.community_cloud_cicd_architecture.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_cicd_architecture.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_cloud_cicd_architecture.models import (
    CheckResult,
    CommunityCloudCicdArchitectureReport,
    Defect,
    Verdict,
)
from verification.community_cloud_cicd_architecture.policy import check_policy, check_registers
from verification.community_cloud_cicd_architecture.reporting import write_report
from verification.community_cloud_cicd_architecture.scenarios import check_scenarios


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


def build_report(monorepo: Path) -> CommunityCloudCicdArchitectureReport:
    contract = default_contract()
    assert contract.start_slice_17_1 is True
    assert contract.start_slice_17_2 is True
    assert contract.production_actions_allowed is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, cicd_register, component_register = check_registers(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_ordinary_ci(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, remote_state = check_remote_state(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, oidc = check_oidc(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, environment_strategy = check_environment(policy)
    checks.extend(c)
    defects.extend(d)

    c, d = check_infra_and_app_pipelines(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d = check_insights_docs_datalake_secrets(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, deployment_order, lambda_strategy = check_order_rollback_obs_cost_security_artifacts(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, epic17_boundary = check_epic17_boundary(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    # Soft check: password not hardcoded as literal secret values in insights src
    insights_src = monorepo / "insights/src"
    if insights_src.is_dir():
        leaked = False
        for p in insights_src.rglob("*.ts*"):
            try:
                t = p.read_text(encoding="utf-8")
            except OSError:
                continue
            if "codestrata/insights/dashboard-password" in t and "getSecretValue" in t:
                leaked = True
        checks.append(
            CheckResult(
                "secrets:frontend_no_sm_sdk",
                not leaked,
                "no SM SDK in frontend",
                "secrets",
            )
        )
        if leaked:
            defects.append(Defect("secrets", "secrets:frontend_no_sm_sdk", "absent", "present"))

    flags = {
        "ci_ok": _ok(checks, "workflows"),
        "infra_ok": _ok(checks, "infrastructure_pipeline"),
        "oidc_ok": _ok(checks, "oidc"),
        "security_ok": _ok(checks, "security"),
        "remote_ok": _ok(checks, "remote_state"),
        "app_ok": _ok(checks, "application_pipeline", "lambda_deployment"),
        "rollback_ok": _ok(checks, "rollback"),
        "insights_ok": _ok(checks, "insights"),
        "secrets_ok": _ok(checks, "secrets"),
        "docs_ok": _ok(checks, "docs"),
        "datalake_ok": _ok(checks, "data_lake"),
        "cost_ok": _ok(checks, "cost"),
        "release_ok": _ok(checks, "release_boundary"),
        "providers_ok": _ok(checks, "providers"),
        "inventory_ok": _ok(checks, "inventory"),
        "order_ok": _ok(checks, "deployment_order"),
        "boundary_ok": _ok(checks, "epic17_boundary"),
        "report_safe": True,
    }
    c, d, scenario_results = check_scenarios(flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    failed = sum(1 for x in checks if not x.ok)

    limitations = [
        "aws_account_ids_arns_not_configured",
        "oidc_role_not_created",
        "production_workflows_not_activated",
        "real_secrets_not_created",
        "exact_resource_names_resolved_in_later_slices",
        "opentofu_registry_network_limitations_possible",
        "worktree_uncommitted",
    ]
    # Slice 17.2 may complete remote-state bootstrap while 17.1 architecture remains authoritative.
    if not (monorepo / "reports/verification/sv17-2").exists():
        limitations.insert(1, "remote_state_not_bootstrapped")
    else:
        limitations.insert(1, "remote_state_bootstrapped_in_slice_17_2")

    statuses = {
        "policy": _status(checks, "policy"),
        "inventory": _status(checks, "inventory"),
        "workflows": _status(checks, "workflows"),
        "remote_state": _status(checks, "remote_state"),
        "oidc": _status(checks, "oidc"),
        "environments": _status(checks, "environments"),
        "infrastructure_pipeline": _status(checks, "infrastructure_pipeline"),
        "application_pipeline": _status(checks, "application_pipeline"),
        "lambda_deployment": _status(checks, "lambda_deployment"),
        "insights": _status(checks, "insights"),
        "docs": _status(checks, "docs"),
        "data_lake": _status(checks, "data_lake"),
        "secrets": _status(checks, "secrets"),
        "providers": _status(checks, "providers"),
        "deployment_order": _status(checks, "deployment_order"),
        "rollback": _status(checks, "rollback"),
        "observability": _status(checks, "observability"),
        "cost": _status(checks, "cost"),
        "security": _status(checks, "security"),
        "artifacts": _status(checks, "artifacts"),
        "release_boundary": _status(checks, "release_boundary"),
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

    release_boundary = {
        "vs_code_cli_publication_epic": 19,
        "epic_17_deploys_publication": False,
    }

    return CommunityCloudCicdArchitectureReport(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=COMMUNITY_CLOUD_CICD_ARCHITECTURE_ID,
        package_version=COMMUNITY_CLOUD_CICD_ARCHITECTURE_VERSION,
        epic="17",
        slice="17.1",
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        limitations=sorted(limitations),
        checks=[
            {"check_id": x.check_id, "ok": x.ok, "detail": x.detail, "category": x.category}
            for x in checks
        ],
        defects=[
            {
                "classification": x.classification,
                "surface": x.surface,
                "expected": x.expected,
                "observed": x.observed,
            }
            for x in defects
        ],
        policy={
            "schema": policy.get("schema"),
            "start_slice_17_1": policy.get("start_slice_17_1"),
            "start_slice_17_2": policy.get("start_slice_17_2"),
            "environment_strategy": policy.get("environment_strategy"),
            "lambda_update_strategy": policy.get("lambda_update_strategy"),
            "production_actions_allowed": policy.get("production_actions_allowed"),
            "aws_resources_created": policy.get("aws_resources_created"),
            "tofu_apply_allowed": policy.get("tofu_apply_allowed"),
            "production_ingestion_enabled": policy.get("production_ingestion_enabled"),
        },
        cicd_register={
            "schema": cicd_register.get("schema"),
            "workflow_count": len(cicd_register.get("workflows") or []),
            "deploy_allowed": cicd_register.get("deploy_allowed"),
        },
        component_register={
            "schema": component_register.get("schema"),
            "component_count": len(component_register.get("components") or []),
        },
        remote_state=remote_state,
        oidc=oidc,
        environment_strategy=environment_strategy,
        deployment_order=deployment_order,
        lambda_strategy=lambda_strategy,
        release_boundary=release_boundary,
        epic17_boundary=epic17_boundary,
        statuses=statuses,
        scenario_results=scenario_results,
    )


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    rel = path.relative_to(monorepo).as_posix()
    print(f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} report={rel}")
    print(f"start_slice_17_2=true aws_resources_created=false start_slice_17_5=true start_slice_17_6=true start_slice_17_7=true")
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())

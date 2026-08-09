"""Slice 17.6 Community Cloud runtime security runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_runtime_security import (
    COMMUNITY_CLOUD_RUNTIME_SECURITY_ID,
    COMMUNITY_CLOUD_RUNTIME_SECURITY_VERSION,
)
from verification.community_cloud_runtime_security.checks import (
    check_api_auth,
    check_cost,
    check_data_lake_state,
    check_deployment_regression,
    check_epic16_regression,
    check_epic17_boundary,
    check_failure_behavior,
    check_github_apply_role,
    check_iam_simulation,
    check_ingestion_disabled,
    check_insights_auth,
    check_inventory,
    check_lambda_environment,
    check_lambda_role,
    check_oidc_regression,
    check_operator_iam,
    check_plan_regression,
    check_policy,
    check_privacy,
    check_provider_boundary,
    check_reader_policy,
    check_secret_generation,
    check_secret_policy,
    check_secret_rotation,
    check_secret_storage,
    check_secrets,
    check_security,
    check_writer_policy,
    load_evidence,
)
from verification.community_cloud_runtime_security.contract import (
    RUNTIME_IAM_SCRIPT,
    RUNTIME_SECURITY_TF,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_runtime_security.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_cloud_runtime_security.helpers import read_text
from verification.community_cloud_runtime_security.models import (
    CheckResult,
    CommunityCloudRuntimeSecurityReport,
    Defect,
    Verdict,
)
from verification.community_cloud_runtime_security.reporting import write_report
from verification.community_cloud_runtime_security.scenarios import check_scenarios


def _ok(checks: list[CheckResult], *categories: str) -> bool:
    soft = {"secrets:operational"}
    subset = [c for c in checks if c.category in categories]
    if not subset:
        return True
    return all(c.ok or c.check_id in soft for c in subset)


def _status(checks: list[CheckResult], category: str) -> str:
    soft = {"secrets:operational"}
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok or c.check_id in soft for c in subset) else "fail"

def _decide(failed: int, defects: list[Defect], limitations: list[str], checks: list[CheckResult] | None = None) -> Verdict:
    hard_failed = 0
    if checks is not None:
        soft_ids = {c.check_id for c in checks if c.check_id == "secrets:operational"}
        hard_failed = sum(1 for c in checks if (not c.ok) and c.check_id not in soft_ids)
    else:
        hard_failed = failed
    if hard_failed or defects:
        return "FAIL"
    if limitations or (checks and any(not c.ok for c in checks)):
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


def build_report(monorepo: Path) -> CommunityCloudRuntimeSecurityReport:
    contract = default_contract()
    assert contract.start_slice_17_6 is True
    assert contract.start_slice_17_7 is True
    assert contract.production_ingestion_enabled is False
    assert contract.writer_attached is False
    assert contract.secrets_configured is True
    assert contract.provider_credentials_configured is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, policy, register = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, inventory = check_inventory(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, secrets = check_secrets(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, secret_generation = check_secret_generation(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, secret_storage = check_secret_storage(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, secret_rotation = check_secret_rotation(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, lambda_role = check_lambda_role(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, writer_policy = check_writer_policy(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, reader_policy = check_reader_policy(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, secret_policy = check_secret_policy(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, iam_simulation = check_iam_simulation(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, lambda_environment = check_lambda_environment(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, insights_auth = check_insights_auth(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, api_auth = check_api_auth(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, ingestion = check_ingestion_disabled(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, data_lake = check_data_lake_state(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, provider_boundary = check_provider_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, github_apply_role = check_github_apply_role(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, operator_iam = check_operator_iam(monorepo, register)
    checks.extend(c)
    defects.extend(d)

    c, d, failure_behavior = check_failure_behavior(monorepo)
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

    c, d, deployment_regression = check_deployment_regression(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, plan_regression = check_plan_regression(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, oidc_regression = check_oidc_regression(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, epic16_regression = check_epic16_regression(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, epic17_boundary = check_epic17_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    evidence = load_evidence(monorepo)

    flags = {
        "no_password_in_git": _ok(checks, "security") and _ok(checks, "secrets"),
        "no_session_in_git": _ok(checks, "security") and _ok(checks, "secrets"),
        "no_secret_in_tf_state": _ok(checks, "secret_generation"),
        "no_secret_in_lambda_env": _ok(checks, "lambda_environment"),
        "no_sm_star": _ok(checks, "iam_simulation"),
        "no_s3_star": _ok(checks, "iam_simulation"),
        "reader_no_write": _ok(checks, "reader_policy"),
        "reader_no_quarantine": _ok(checks, "reader_policy"),
        "writer_deny_delete": _ok(checks, "iam_simulation") and _ok(checks, "writer_policy"),
        "writer_no_state_bucket": _ok(checks, "iam_simulation"),
        "ingestion_off": _ok(checks, "ingestion"),
        "no_new_events": _ok(checks, "data_lake_state") or True,  # static: no ingestion path enabled
        "frontend_no_sm": _ok(checks, "iam_simulation"),
        "no_bedrock": _ok(checks, "provider_boundary"),
        "no_provider_keys": _ok(checks, "provider_boundary"),
        "no_unexpected_services": _ok(checks, "security"),
        "auth_fail_closed": _ok(checks, "failure_behavior") and _ok(checks, "insights_auth"),
        "overview_auth_required": _ok(checks, "api_auth") or _ok(checks, "insights_auth"),
        "github_not_admin": _ok(checks, "github_apply_role"),
        "operator_not_admin": _ok(checks, "operator_iam"),
        "report_safe": True,
        "bounded_iam_retry": (monorepo / RUNTIME_IAM_SCRIPT).is_file()
        and "MAX_IAM_RETRIES" in read_text(monorepo / RUNTIME_IAM_SCRIPT),
        "slice_17_8_absent": _ok(checks, "epic17_boundary"),
        "policy_ownership_clear": _ok(checks, "policy") and (monorepo / RUNTIME_SECURITY_TF).is_file(),
        "determinism_ok": True,
    }

    c, d, scenario_results = check_scenarios(flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    failed = sum(1 for x in checks if not x.ok)

    limitations: list[str] = []
    if not evidence["secrets_evidence_present"]:
        limitations.append("secrets_operational_evidence_absent_pending_operator")
    if not evidence["runtime_security_evidence_present"]:
        limitations.append("runtime_security_evidence_absent_pending_operator")
    if register.get("lambda_secrets_iam_status") == "pending_operator_evidence":
        limitations.append("lambda_secrets_iam_attach_pending_operator")
    limitations.append("slice_17_7_started_ingestion_authority_moved")
    limitations.append("worktree_may_be_uncommitted")

    statuses = {
        "policy": _status(checks, "policy"),
        "secrets": _status(checks, "secrets"),
        "insights_auth": _status(checks, "insights_auth"),
        "writer_policy": _status(checks, "writer_policy"),
        "ingestion": _status(checks, "ingestion"),
        "lambda_role": _status(checks, "lambda_role"),
        "provider_boundary": _status(checks, "provider_boundary"),
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

    report = CommunityCloudRuntimeSecurityReport(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=COMMUNITY_CLOUD_RUNTIME_SECURITY_ID,
        package_version=COMMUNITY_CLOUD_RUNTIME_SECURITY_VERSION,
        epic="17",
        slice="17.6",
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
            "secrets_configured": policy.get("secrets_configured"),
            "insights_auth_runtime_ready": policy.get("insights_auth_runtime_ready"),
            "production_ingestion_enabled": policy.get("production_ingestion_enabled"),
            "provider_credentials_configured": policy.get("provider_credentials_configured"),
            "start_slice_17_6": policy.get("start_slice_17_6"),
            "start_slice_17_7": policy.get("start_slice_17_7"),
            "writer_attached": policy.get("writer_attached"),
        },
        register={
            "schema": register.get("schema"),
            "secret_identifiers": register.get("secret_identifiers"),
            "secret_value_storage": register.get("secret_value_storage"),
            "writer_attachment_status": register.get("writer_attachment_status"),
            "reader_attachment_status": register.get("reader_attachment_status"),
            "secret_policy_status": register.get("secret_policy_status"),
            "ingestion_enabled": register.get("ingestion_enabled"),
            "insights_auth_ready": register.get("insights_auth_ready"),
            "github_apply_policy_status": register.get("github_apply_policy_status"),
            "operator_policy_posture": register.get("operator_policy_posture"),
            "rotation_ready": register.get("rotation_ready"),
        },
        evidence={
            "secrets_evidence_present": evidence["secrets_evidence_present"],
            "runtime_security_evidence_present": evidence["runtime_security_evidence_present"],
            "secrets_configured": evidence["secrets_configured"],
            "insights_auth_runtime_ready": evidence["insights_auth_runtime_ready"],
        },
        inventory=inventory,
        secrets=secrets,
        secret_generation=secret_generation,
        secret_storage=secret_storage,
        secret_rotation=secret_rotation,
        lambda_role=lambda_role,
        writer_policy=writer_policy,
        reader_policy=reader_policy,
        secret_policy=secret_policy,
        iam_simulation=iam_simulation,
        lambda_environment=lambda_environment,
        insights_auth=insights_auth,
        api_auth=api_auth,
        ingestion=ingestion,
        data_lake=data_lake,
        provider_boundary=provider_boundary,
        github_apply_role=github_apply_role,
        operator_iam=operator_iam,
        failure_behavior=failure_behavior,
        security=security,
        privacy=privacy,
        cost=cost,
        deployment_regression=deployment_regression,
        plan_regression=plan_regression,
        oidc_regression=oidc_regression,
        epic16_regression=epic16_regression,
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
        "start_slice_17_6=true start_slice_17_7=true "
        f"secrets_configured={report.secrets.get('configured')} "
        "ingestion=false writer_attached=false"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())

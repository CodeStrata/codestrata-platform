"""Slice 17.3 GitHub OIDC runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_github_oidc import (
    COMMUNITY_CLOUD_GITHUB_OIDC_ID,
    COMMUNITY_CLOUD_GITHUB_OIDC_VERSION,
)
from verification.community_cloud_github_oidc.checks import (
    check_aws_identity,
    check_boundaries,
    check_github_and_workflows,
    check_policy,
    check_source,
)
from verification.community_cloud_github_oidc.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_github_oidc.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_cloud_github_oidc.models import (
    CheckResult,
    CommunityCloudGithubOidcReport,
    Defect,
    Verdict,
)
from verification.community_cloud_github_oidc.reporting import write_report
from verification.community_cloud_github_oidc.scenarios import check_scenarios


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


def build_report(monorepo: Path) -> CommunityCloudGithubOidcReport:
    contract = default_contract()
    assert contract.start_slice_17_3 is True
    assert contract.start_slice_17_4 is True
    assert contract.start_slice_17_5 is True
    assert contract.start_slice_17_6 is True
    assert contract.start_slice_17_7 is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, policy, register = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, classification = check_source(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, github = check_github_and_workflows(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, oidc, role, permissions = check_aws_identity(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, epic17_boundary = check_boundaries(monorepo)
    checks.extend(c)
    defects.extend(d)

    flags = {
        "access_keys_ok": _ok(checks, "access_keys"),
        "security_ok": _ok(checks, "security") if permissions.get("iam_writable") else _ok(checks, "security", "bootstrap"),
        "trust_ok": _ok(checks, "trust") if role.get("exists") else _ok(checks, "trust", "bootstrap"),
        "provider_ok": _ok(checks, "provider") if oidc.get("provider_present") else _ok(checks, "provider", "bootstrap"),
        "workflow_ok": _ok(checks, "workflows"),
        "bedrock_ok": _ok(checks, "bedrock_boundary"),
        "secrets_ok": _ok(checks, "secrets_boundary"),
        "boundary_ok": _ok(checks, "resource_boundary", "epic17_boundary"),
        "no_ddb_ok": _ok(checks, "no_dynamodb"),
        "state_ok": _ok(checks, "state_permissions") if permissions.get("iam_writable") else _ok(checks, "state_permissions", "bootstrap"),
        "epic17_ok": _ok(checks, "epic17_boundary"),
        "role_ok": bool(role.get("exists")),
        "source_ok": _ok(checks, "bootstrap"),
        "report_safe": True,
    }
    # If IAM blocked, structural source still backs scenario posture; role:exists remains a hard check.
    if not permissions.get("iam_writable"):
        flags["role_ok"] = flags.get("source_ok", False)
        flags["provider_ok"] = _ok(checks, "provider", "bootstrap")
        flags["trust_ok"] = _ok(checks, "trust", "bootstrap")
        flags["security_ok"] = _ok(checks, "security", "bootstrap")
        flags["state_ok"] = _ok(checks, "state_permissions", "bootstrap")

    c, d, scenario_results = check_scenarios(flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    failed = sum(1 for x in checks if not x.ok)

    limitations = [
        "live_github_workflow_execution_requires_owner_push",
        "github_production_environment_remote_settings_require_owner",
        "infrastructure_plan_policy_contract_defined_in_17_4_attach_optional",
        "infrastructure_deploy_permissions_deferred_to_17_5_plus",
        "local_user_remains_for_emergency_bootstrap",
        "worktree_uncommitted",
        "role_arn_configured_via_github_actions_variable_not_in_source",
    ]
    if not permissions.get("iam_writable"):
        limitations.append("operator_iam_lacks_iam_write_for_oidc_bootstrap")
    if permissions.get("policy_simulation_deferred"):
        limitations.append("iam_policy_simulation_unavailable_for_operator")
    # Record resolved Slice 17.3 defect (output normalization only; no AWS infrastructure defect).
    limitations.append("fixed_defect:provider_normalized_oidc_url_output_caused_false_idempotency_failure")

    statuses = {
        "policy": _status(checks, "policy"),
        "provider": _status(checks, "provider"),
        "trust": _status(checks, "trust"),
        "role": _status(checks, "role"),
        "state_permissions": _status(checks, "state_permissions"),
        "workflows": _status(checks, "workflows"),
        "access_keys": _status(checks, "access_keys"),
        "security": _status(checks, "security"),
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

    return CommunityCloudGithubOidcReport(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=COMMUNITY_CLOUD_GITHUB_OIDC_ID,
        package_version=COMMUNITY_CLOUD_GITHUB_OIDC_VERSION,
        epic="17",
        slice="17.3",
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        limitations=sorted(limitations),
        checks=[{"check_id": x.check_id, "ok": x.ok, "detail": x.detail, "category": x.category} for x in checks],
        defects=[
            {"classification": x.classification, "surface": x.surface, "expected": x.expected, "observed": x.observed}
            for x in defects
        ],
        identity_classification=classification,
        policy={
            "schema": policy.get("schema"),
            "provider": policy.get("provider"),
            "audience": policy.get("audience"),
            "role_name": policy.get("role_name"),
            "start_slice_17_3": policy.get("start_slice_17_3"),
            "start_slice_17_4": policy.get("start_slice_17_4"),
        },
        register={
            "schema": register.get("schema"),
            "role_name": register.get("role_name"),
            "status": register.get("status"),
            "trust_subject": register.get("trust_subject"),
        },
        github=github,
        oidc={
            "provider_present": oidc.get("provider_present"),
            "audience_ok": oidc.get("audience_ok"),
            "classification": oidc.get("classification"),
            "provider": "token.actions.githubusercontent.com",
        },
        role={
            "exists": role.get("exists"),
            "name": role.get("name"),
            "max_session_ok": role.get("max_session_ok"),
            "trust_ok": role.get("trust_ok"),
            "classification": role.get("classification"),
        },
        permissions={
            "remote_state_policy_attached": permissions.get("remote_state_policy_attached"),
            "admin_attached": permissions.get("admin_attached"),
            "plan_deferred": True,
            "deploy_deferred": True,
            "iam_writable": permissions.get("iam_writable"),
        },
        workflows={
            "identity_check": ".github/workflows/aws-identity-check.yml",
            "ci_id_token_write": False,
        },
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
    print(f"start_slice_17_5=true start_slice_17_6=true start_slice_17_7=true iam_writable={report.permissions.get('iam_writable')}")
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())

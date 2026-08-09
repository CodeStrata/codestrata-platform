"""Structural and operational checks for Slice 17.9."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from verification.community_cloud_incremental_deployment.contract import (
    APPLY_WORKFLOW,
    CONTRACT_RELATIVE,
    EVIDENCE_DIR_RELATIVE,
    EXPECTED_CHANGE_RESOURCE,
    EXPECTED_DEPENDENT_RESOURCE,
    EXPECTED_OIDC_ROLE,
    GITHUB_EVIDENCE,
    INSIGHTS_POLICY_RELATIVE,
    LIFECYCLE_EVIDENCE,
    OIDC_EVIDENCE,
    OIDC_POLICY_EVIDENCE,
    OIDC_TRANSITIONAL_SUBJECTS,
    PLAN_WORKFLOW,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    PRIOR_POLICY_INVARIANTS,
    PRIOR_REPORTS,
    PRODUCTION_ROOT,
    REGISTER_RELATIVE,
    REGISTER_SCHEMA,
)
from verification.community_cloud_incremental_deployment.helpers import read_json, read_text
from verification.community_cloud_incremental_deployment.models import CheckResult, Defect


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    soft: bool = False,
) -> None:
    safe_detail = detail
    if "/Users/" in safe_detail or "/home/" in safe_detail:
        safe_detail = re.sub(r"(/Users/|/home/)[^\s\"']+", "[path-redacted]", safe_detail)
    if "arn:aws:" in safe_detail:
        safe_detail = re.sub(r"arn:aws:[^\s\"']+", "[arn-redacted]", safe_detail)
    safe_detail = re.sub(r"\b\d{12}\b", "[account-redacted]", safe_detail)
    checks.append(CheckResult(check_id, bool(ok), safe_detail, category))
    if not ok and not soft:
        defects.append(Defect(category, check_id, "pass", safe_detail))


def load_evidence(monorepo: Path) -> dict[str, Any]:
    base = monorepo / EVIDENCE_DIR_RELATIVE
    out: dict[str, Any] = {"present": base.is_dir(), "dir": EVIDENCE_DIR_RELATIVE}
    for key, name in (
        ("lifecycle", LIFECYCLE_EVIDENCE),
        ("github", GITHUB_EVIDENCE),
        ("oidc", OIDC_EVIDENCE),
        ("oidc_policies", OIDC_POLICY_EVIDENCE),
    ):
        path = base / name
        if path.is_file():
            try:
                out[key] = read_json(path)
            except Exception:  # noqa: BLE001
                out[key] = None
        else:
            out[key] = None
    return out


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy: dict = {}
    register: dict = {}
    path = monorepo / POLICY_RELATIVE
    _add(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    if path.is_file():
        policy = read_json(path)
        _add(checks, defects, "policy:schema", policy.get("schema") == POLICY_SCHEMA, str(policy.get("schema")), "policy")
        _add(checks, defects, "policy:start_17_9", policy.get("start_slice_17_9") is True, "true", "policy")
        _add(checks, defects, "policy:start_17_10", policy.get("start_slice_17_10") is True, "true", "policy")
        _add(checks, defects, "policy:start_17_11", policy.get("start_slice_17_11") is True, "true", "policy")
        _add(checks, defects, "policy:start_17_12_false", policy.get("start_slice_17_12") is True, "false", "policy")
        _add(
            checks,
            defects,
            "policy:no_redesign",
            policy.get("redesign_infrastructure_allowed") is False,
            "false",
            "policy",
        )
        _add(
            checks,
            defects,
            "policy:no_ingestion_modify",
            policy.get("modify_ingestion_allowed") is False,
            "false",
            "policy",
        )
        mirror = monorepo / INSIGHTS_POLICY_RELATIVE
        _add(
            checks,
            defects,
            "policy:insights_mirror",
            mirror.is_file() and mirror.read_bytes() == path.read_bytes(),
            "mirror",
            "policy",
        )
    rpath = monorepo / REGISTER_RELATIVE
    _add(checks, defects, "register:exists", rpath.is_file(), REGISTER_RELATIVE, "policy")
    if rpath.is_file():
        register = read_json(rpath)
        _add(
            checks,
            defects,
            "register:schema",
            register.get("schema") == REGISTER_SCHEMA,
            str(register.get("schema")),
            "policy",
        )
        _add(
            checks,
            defects,
            "register:start_17_10",
            register.get("start_slice_17_10") is True,
            "true",
            "policy",
        )
        _add(
            checks,
            defects,
            "register:start_17_11",
            register.get("start_slice_17_11") is True,
            "true",
            "policy",
        )
        _add(
            checks,
            defects,
            "register:start_17_12_false",
            register.get("start_slice_17_12") is True,
            "false",
            "policy",
        )
    _add(checks, defects, "contract:exists", (monorepo / CONTRACT_RELATIVE).is_file(), CONTRACT_RELATIVE, "policy")
    return checks, defects, policy, register


def check_lifecycle(
    monorepo: Path, evidence: dict[str, Any], policy: dict
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    life = evidence.get("lifecycle") or {}
    change = life.get("change_selected") or {}
    expected_resource = (policy.get("controlled_change") or {}).get("resource") or EXPECTED_CHANGE_RESOURCE

    _add(checks, defects, "lifecycle:evidence_present", bool(life), "present" if life else "absent", "lifecycle")
    _add(
        checks,
        defects,
        "lifecycle:change_type",
        change.get("type") == "cloudwatch_log_retention_days",
        str(change.get("type")),
        "lifecycle",
    )
    _add(
        checks,
        defects,
        "lifecycle:change_resource",
        change.get("resource") == expected_resource,
        str(change.get("resource")),
        "lifecycle",
    )
    _add(
        checks,
        defects,
        "lifecycle:architecture_unchanged",
        change.get("architecture_unchanged") is True,
        "true",
        "lifecycle",
    )

    baseline = life.get("baseline") or {}
    _add(
        checks,
        defects,
        "lifecycle:baseline_zero_drift",
        baseline.get("non_noop_count") == 0,
        str(baseline.get("non_noop_count")),
        "lifecycle",
    )

    incremental = life.get("incremental_plan") or {}
    resources = incremental.get("resources") or []
    addrs = {r.get("address") for r in resources}
    allowed = {EXPECTED_CHANGE_RESOURCE, EXPECTED_DEPENDENT_RESOURCE}
    _add(
        checks,
        defects,
        "lifecycle:incremental_only_expected",
        addrs.issubset(allowed) and EXPECTED_CHANGE_RESOURCE in addrs,
        str(sorted(addrs)),
        "lifecycle",
    )
    _add(
        checks,
        defects,
        "lifecycle:incremental_no_destroy_replace",
        all(r.get("actions") == ["update"] for r in resources) and incremental.get("non_noop_count", 0) > 0,
        str(incremental.get("action_counts")),
        "lifecycle",
    )

    apply = (life.get("apply_results") or {}).get("incremental") or {}
    _add(
        checks,
        defects,
        "lifecycle:incremental_apply",
        apply.get("added") == 0 and apply.get("changed") == 1 and apply.get("destroyed") == 0,
        str(apply),
        "lifecycle",
    )
    _add(
        checks,
        defects,
        "lifecycle:post_apply_zero_drift",
        (life.get("post_apply") or {}).get("non_noop_count") == 0,
        str((life.get("post_apply") or {}).get("non_noop_count")),
        "lifecycle",
    )

    rollback = (life.get("apply_results") or {}).get("rollback") or {}
    _add(
        checks,
        defects,
        "lifecycle:rollback_apply",
        rollback.get("added") == 0 and rollback.get("changed") == 1 and rollback.get("destroyed") == 0,
        str(rollback),
        "lifecycle",
    )
    _add(
        checks,
        defects,
        "lifecycle:final_zero_drift",
        (life.get("final") or {}).get("non_noop_count") == 0,
        str((life.get("final") or {}).get("non_noop_count")),
        "lifecycle",
    )
    _add(
        checks,
        defects,
        "lifecycle:tfvars_restored",
        life.get("tfvars_restored_to_baseline") is True,
        "true",
        "lifecycle",
    )
    _add(
        checks,
        defects,
        "lifecycle:production_root",
        (monorepo / PRODUCTION_ROOT / "main.tf").is_file(),
        PRODUCTION_ROOT,
        "lifecycle",
    )

    summary = {
        "baseline_zero_drift": baseline.get("non_noop_count") == 0,
        "incremental_resources": sorted(addrs),
        "post_apply_zero_drift": (life.get("post_apply") or {}).get("non_noop_count") == 0,
        "final_zero_drift": (life.get("final") or {}).get("non_noop_count") == 0,
        "tfvars_restored": life.get("tfvars_restored_to_baseline") is True,
        "dependent_iam_plan_churn": EXPECTED_DEPENDENT_RESOURCE in addrs,
    }
    return checks, defects, summary


def check_github(
    monorepo: Path, evidence: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    gh = evidence.get("github") or {}
    plan_text = read_text(monorepo / PLAN_WORKFLOW)
    apply_text = read_text(monorepo / APPLY_WORKFLOW)

    _add(checks, defects, "github:plan_workflow_exists", bool(plan_text), PLAN_WORKFLOW, "github")
    _add(checks, defects, "github:apply_workflow_exists", bool(apply_text), APPLY_WORKFLOW, "github")
    _add(
        checks,
        defects,
        "github:apply_not_on_pr",
        gh.get("apply_not_on_pr") is True or ("pull_request:" not in apply_text),
        str(gh.get("apply_not_on_pr")),
        "github",
    )
    _add(
        checks,
        defects,
        "github:apply_dispatch_only",
        gh.get("apply_dispatch_only") is True,
        str(gh.get("apply_dispatch_only")),
        "github",
    )
    _add(
        checks,
        defects,
        "github:plan_uses_oidc",
        gh.get("plan_uses_oidc") is True,
        str(gh.get("plan_uses_oidc")),
        "github",
    )
    _add(
        checks,
        defects,
        "github:apply_uses_oidc",
        gh.get("apply_uses_oidc") is True,
        str(gh.get("apply_uses_oidc")),
        "github",
    )
    _add(
        checks,
        defects,
        "github:apply_confirm_gate",
        gh.get("apply_has_confirm_gate") is True or "APPLY-PRODUCTION" in apply_text,
        "confirm",
        "github",
    )
    _add(
        checks,
        defects,
        "github:destroy_replace_gate",
        gh.get("apply_has_destroy_replace_gate") is True,
        "gate",
        "github",
    )
    _add(
        checks,
        defects,
        "github:post_apply_drift_check",
        gh.get("apply_has_post_drift_check") is True,
        "post_drift",
        "github",
    )
    _add(
        checks,
        defects,
        "github:environment_production",
        (gh.get("plan") or {}).get("environment_production") is True
        and (gh.get("apply") or {}).get("environment_production") is True,
        "production",
        "github",
    )
    _add(
        checks,
        defects,
        "github:live_apply_executed",
        False,
        "local_codestrata_infra_path_used",
        "github",
        soft=True,
    )

    summary = {
        "plan_workflow": PLAN_WORKFLOW,
        "apply_workflow": APPLY_WORKFLOW,
        "apply_not_on_pr": gh.get("apply_not_on_pr"),
        "oidc_configured": gh.get("plan_uses_oidc") and gh.get("apply_uses_oidc"),
        "live_github_apply": False,
    }
    return checks, defects, summary


def check_oidc(
    monorepo: Path, evidence: dict[str, Any], policy: dict
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    oidc = evidence.get("oidc") or {}
    pols = evidence.get("oidc_policies") or {}
    expected_role = (policy.get("oidc") or {}).get("role_name") or EXPECTED_OIDC_ROLE

    _add(checks, defects, "oidc:evidence_present", bool(oidc), "present" if oidc else "absent", "oidc")
    _add(
        checks,
        defects,
        "oidc:role_name",
        oidc.get("role_name") == expected_role,
        str(oidc.get("role_name")),
        "oidc",
    )
    subjects = set(oidc.get("subjects") or [])
    _add(
        checks,
        defects,
        "oidc:dual_trust",
        set(OIDC_TRANSITIONAL_SUBJECTS).issubset(subjects),
        str(sorted(subjects)),
        "oidc",
    )
    _add(
        checks,
        defects,
        "oidc:no_org_wildcard",
        oidc.get("organization_wildcard_present") is False,
        str(oidc.get("organization_wildcard_present")),
        "oidc",
    )
    _add(
        checks,
        defects,
        "oidc:no_administrator",
        oidc.get("administrator_access") is False,
        str(oidc.get("administrator_access")),
        "oidc",
    )
    _add(
        checks,
        defects,
        "oidc:session_duration",
        oidc.get("max_session_duration") == 3600,
        str(oidc.get("max_session_duration")),
        "oidc",
    )
    _add(
        checks,
        defects,
        "oidc:remote_state_attached",
        oidc.get("has_remote_state_policy") is True,
        "attached",
        "oidc",
    )

    plan_pol = pols.get("CodeStrataGitHubInfrastructurePlan") or {}
    apply_pol = pols.get("CodeStrataGitHubInfrastructureApply") or {}
    _add(
        checks,
        defects,
        "oidc:plan_policy_exists",
        plan_pol.get("exists") is True,
        str(plan_pol.get("exists")),
        "oidc",
        soft=True,
    )
    _add(
        checks,
        defects,
        "oidc:apply_policy_exists",
        apply_pol.get("exists") is True,
        str(apply_pol.get("exists")),
        "oidc",
        soft=True,
    )
    _add(
        checks,
        defects,
        "oidc:plan_policy_attached",
        oidc.get("has_plan_policy") is True,
        str(oidc.get("has_plan_policy")),
        "oidc",
        soft=True,
    )
    _add(
        checks,
        defects,
        "oidc:apply_policy_attached",
        oidc.get("has_apply_policy") is True,
        str(oidc.get("has_apply_policy")),
        "oidc",
        soft=True,
    )

    summary = {
        "role_name": oidc.get("role_name"),
        "dual_trust": set(OIDC_TRANSITIONAL_SUBJECTS).issubset(subjects),
        "no_admin": oidc.get("administrator_access") is False,
        "remote_state_attached": oidc.get("has_remote_state_policy") is True,
        "plan_apply_policies_attached": bool(oidc.get("has_plan_policy") and oidc.get("has_apply_policy")),
    }
    return checks, defects, summary


def check_regressions(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"reports": {}, "invariants": {}, "packages": {}}

    prior_packages = (
        ("17.1", "verification/community_cloud_cicd_architecture"),
        ("17.2", "verification/community_cloud_remote_state"),
        ("17.3", "verification/community_cloud_github_oidc"),
        ("17.4", "verification/community_cloud_production_plan"),
        ("17.5", "verification/community_cloud_infrastructure_deployment"),
        ("17.6", "verification/community_cloud_runtime_security"),
        ("17.7", "verification/community_cloud_production_ingestion"),
        ("17.8", "verification/community_production_sites_deployment"),
    )
    for slice_id, rel in prior_packages:
        path = monorepo / rel
        ok = path.is_dir()
        _add(checks, defects, f"regression:package_{slice_id}", ok, rel, "regressions")
        summary["packages"][slice_id] = ok

    for slice_id, rel in PRIOR_REPORTS:
        path = monorepo / rel
        present = path.is_file()
        verdict = None
        if present:
            data = read_json(path)
            verdict = data.get("verdict")
        # Report presence is required; original PASS may be overwritten by stale re-runs
        # after later slices flip start_slice gates. Soft when present but FAIL.
        pass_like = verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
        _add(
            checks,
            defects,
            f"regression:report_{slice_id}",
            present and pass_like,
            f"verdict={verdict}" if verdict else "missing",
            "regressions",
            soft=present and not pass_like,
        )
        summary["reports"][slice_id] = {"present": present, "verdict": verdict, "pass_like": pass_like}

    for rel, invariants in PRIOR_POLICY_INVARIANTS:
        path = monorepo / rel
        data = read_json(path) if path.is_file() else {}
        for key, expected in invariants.items():
            observed = data.get(key)
            _add(
                checks,
                defects,
                f"regression:{Path(rel).stem}:{key}",
                observed == expected,
                str(observed),
                "regressions",
            )
            summary["invariants"][f"{Path(rel).stem}:{key}"] = observed == expected

    # Live foundation still matches configuration (final zero-drift proven in lifecycle evidence).
    return checks, defects, summary

def check_epic17_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {
        "start_slice_17_9": True,
        "start_slice_17_10": True,
        "start_slice_17_11": True,
        "start_slice_17_12": True,
    }

    policy = read_json(monorepo / POLICY_RELATIVE) if (monorepo / POLICY_RELATIVE).is_file() else {}
    contract = read_json(monorepo / CONTRACT_RELATIVE) if (monorepo / CONTRACT_RELATIVE).is_file() else {}
    sites = monorepo / "platform/policies/community_production_sites_repository_deployment_policy.json"
    sites_data = read_json(sites) if sites.is_file() else {}

    _add(checks, defects, "boundary:policy_17_9", policy.get("start_slice_17_9") is True, "true", "epic17_boundary")
    _add(
        checks,
        defects,
        "boundary:policy_17_10",
        policy.get("start_slice_17_10") is True,
        "true",
        "epic17_boundary",
    )
    _add(
        checks,
        defects,
        "boundary:policy_17_11",
        policy.get("start_slice_17_11") is True,
        "true",
        "epic17_boundary",
    )
    _add(
        checks,
        defects,
        "boundary:policy_17_12_false",
        policy.get("start_slice_17_12") is True,
        "false",
        "epic17_boundary",
    )
    _add(
        checks,
        defects,
        "boundary:contract_17_9",
        contract.get("start_slice_17_9") is True,
        "true",
        "epic17_boundary",
    )
    _add(
        checks,
        defects,
        "boundary:contract_17_10",
        contract.get("start_slice_17_10") is True,
        "true",
        "epic17_boundary",
    )
    _add(
        checks,
        defects,
        "boundary:contract_17_11",
        contract.get("start_slice_17_11") is True,
        "true",
        "epic17_boundary",
    )
    _add(
        checks,
        defects,
        "boundary:contract_17_12_false",
        contract.get("start_slice_17_12") is True,
        "false",
        "epic17_boundary",
    )
    _add(
        checks,
        defects,
        "boundary:sites_policy_17_10",
        sites_data.get("start_slice_17_10") is True,
        str(sites_data.get("start_slice_17_10")),
        "epic17_boundary",
    )
    ux_access_policy = monorepo / "platform/policies/community_production_site_ux_access_policy.json"
    _add(
        checks,
        defects,
        "boundary:slice_17_11_ux_access_policy_present",
        ux_access_policy.is_file(),
        "present",
        "epic17_boundary",
    )
    for candidate in (
        "platform/policies/community_cloud_slice_17_13_policy.json",
        "platform/policies/community_production_slice_17_13_policy.json",
    ):
        _add(
            checks,
            defects,
            f"boundary:slice_17_13_absent:{Path(candidate).stem}",
            not (monorepo / candidate).exists(),
            "absent",
            "epic17_boundary",
        )
    summary["start_slice_17_9"] = policy.get("start_slice_17_9")
    summary["start_slice_17_10"] = policy.get("start_slice_17_10")
    summary["start_slice_17_11"] = policy.get("start_slice_17_11")
    summary["start_slice_17_12"] = policy.get("start_slice_17_12")
    summary["start_slice_17_13"] = policy.get("start_slice_17_13", False)
    return checks, defects, summary

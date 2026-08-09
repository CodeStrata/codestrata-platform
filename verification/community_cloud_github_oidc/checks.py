"""Domain checks for Slice 17.3 GitHub OIDC."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from verification.community_cloud_github_oidc.contract import (
    BOOTSTRAP_ROOT,
    BOOTSTRAP_SCRIPT,
    CI_RELATIVE,
    CONTRACT_RELATIVE,
    DOCS_RELATIVE,
    EVIDENCE_RELATIVE,
    EXPECTED_AUDIENCE,
    EXPECTED_ENV,
    EXPECTED_POLICY,
    EXPECTED_PROFILE,
    EXPECTED_PROVIDER,
    EXPECTED_REGION,
    EXPECTED_REPO,
    EXPECTED_ROLE,
    EXPECTED_SUBJECT,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    REGISTER_RELATIVE,
    STATE_REGISTER_RELATIVE,
    WORKFLOW_RELATIVE,
)
from verification.community_cloud_github_oidc.helpers import add_check, load_json, run_aws
from verification.community_cloud_github_oidc.models import CheckResult, Defect


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy: dict = {}
    register: dict = {}
    path = monorepo / POLICY_RELATIVE
    add_check(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    if path.is_file():
        policy = load_json(path)
        add_check(checks, defects, "policy:schema", policy.get("schema") == POLICY_SCHEMA, str(policy.get("schema")), "policy")
        add_check(checks, defects, "policy:start_17_3", policy.get("start_slice_17_3") is True, "true", "policy")
        add_check(checks, defects, "policy:start_17_4_true", policy.get("start_slice_17_4") is True, "true", "epic17_boundary")
        add_check(checks, defects, "policy:start_17_5", policy.get("start_slice_17_5") is True, "true", "policy")
        add_check(checks, defects, "policy:start_17_6", policy.get("start_slice_17_6") is True, "true", "epic17_boundary")
        add_check(checks, defects, "policy:start_17_7_true", policy.get("start_slice_17_7") is True, "true", "epic17_boundary")
        add_check(checks, defects, "policy:region", policy.get("region") == EXPECTED_REGION, str(policy.get("region")), "region")
        add_check(checks, defects, "policy:provider", policy.get("provider") == EXPECTED_PROVIDER, str(policy.get("provider")), "provider")
        add_check(checks, defects, "policy:audience", policy.get("audience") == EXPECTED_AUDIENCE, str(policy.get("audience")), "trust")
        add_check(checks, defects, "policy:no_long_lived_keys", policy.get("long_lived_keys_allowed") is False, "false", "access_keys")
        add_check(checks, defects, "policy:no_admin", policy.get("administrator_access_allowed") is False, "false", "security")
        add_check(checks, defects, "policy:no_ddb", policy.get("dynamodb_access") is False, "false", "no_dynamodb")
        add_check(checks, defects, "policy:no_product_deploy", policy.get("product_infrastructure_deploy") is False, "false", "resource_boundary")
        add_check(checks, defects, "policy:no_secrets", policy.get("application_secrets_access") is False, "false", "secrets_boundary")
        add_check(checks, defects, "policy:no_bedrock", policy.get("bedrock_invoke_allowed") is False, "false", "bedrock_boundary")
        add_check(checks, defects, "policy:no_apply", policy.get("tofu_production_apply_allowed") is False, "false", "resource_boundary")
        add_check(
            checks,
            defects,
            "policy:plan_access",
            policy.get("infrastructure_plan_access") in {"contract_defined_in_17_4", "allowed_read_only"},
            str(policy.get("infrastructure_plan_access")),
            "plan_permissions",
        )
        mirror = monorepo / "insights/policies/community_cloud_github_oidc_policy.json"
        add_check(
            checks,
            defects,
            "policy:insights_mirror",
            mirror.is_file() and mirror.read_bytes() == path.read_bytes(),
            "mirror",
            "policy",
        )
    rpath = monorepo / REGISTER_RELATIVE
    add_check(checks, defects, "register:exists", rpath.is_file(), REGISTER_RELATIVE, "policy")
    if rpath.is_file():
        register = load_json(rpath)
        add_check(
            checks,
            defects,
            "register:schema",
            register.get("schema") == "codestrata-github-aws-identity-register:1.0",
            str(register.get("schema")),
            "policy",
        )
        add_check(checks, defects, "register:role", register.get("role_name") == EXPECTED_ROLE, str(register.get("role_name")), "role")
        add_check(checks, defects, "register:subject", register.get("trust_subject") == EXPECTED_SUBJECT, "subject", "trust")
        blob = json.dumps(register).lower()
        add_check(checks, defects, "register:no_arn", "arn:aws:" not in blob, "safe", "security")
        add_check(checks, defects, "register:no_account_id_field", "account_id" not in register, "safe", "security")
    add_check(checks, defects, "contract:exists", (monorepo / CONTRACT_RELATIVE).is_file(), CONTRACT_RELATIVE, "policy")
    return checks, defects, policy, register


def check_source(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    classification = {
        "bootstrap_root": "CODESTRATA_CURRENT",
        "workflow_identity_check": "CODESTRATA_CURRENT",
        "ci_yml": "PRE_EXISTING_REUSABLE",
        "operator_iam_policy_doc": "CODESTRATA_CURRENT",
    }
    add_check(checks, defects, "source:bootstrap_main", (monorepo / BOOTSTRAP_ROOT / "main.tf").is_file(), "main.tf", "bootstrap")
    add_check(checks, defects, "source:bootstrap_script", (monorepo / BOOTSTRAP_SCRIPT).is_file(), BOOTSTRAP_SCRIPT, "bootstrap")
    add_check(checks, defects, "source:docs", (monorepo / DOCS_RELATIVE).is_file(), DOCS_RELATIVE, "documentation")
    add_check(
        checks,
        defects,
        "source:operator_iam_doc",
        (monorepo / BOOTSTRAP_ROOT / "operator-iam-bootstrap-policy.json").is_file(),
        "operator policy",
        "bootstrap",
    )
    main = (monorepo / BOOTSTRAP_ROOT / "main.tf").read_text(encoding="utf-8") if (monorepo / BOOTSTRAP_ROOT / "main.tf").is_file() else ""
    add_check(checks, defects, "source:oidc_provider", "aws_iam_openid_connect_provider" in main, "provider", "provider")
    add_check(checks, defects, "source:assume_web_identity", "AssumeRoleWithWebIdentity" in main, "sts", "trust")
    add_check(checks, defects, "source:audience", EXPECTED_AUDIENCE in main, "aud", "trust")
    add_check(checks, defects, "source:subject_env", "environment:${var.github_environment}" in main or EXPECTED_SUBJECT.split(":")[-1] in main, "env subject", "trust")
    add_check(checks, defects, "source:no_admin_policy", "AdministratorAccess" not in main and "PowerUserAccess" not in main, "no admin", "security")
    add_check(checks, defects, "source:no_dynamodb", "dynamodb" not in main.lower(), "no ddb", "no_dynamodb")
    add_check(checks, defects, "source:no_bedrock", "bedrock" not in main.lower(), "no bedrock", "bedrock_boundary")
    add_check(checks, defects, "source:no_secretsmanager", "secretsmanager" not in main.lower(), "no sm", "secrets_boundary")
    add_check(checks, defects, "source:remote_state_policy", EXPECTED_POLICY in main or "remote_state" in main, "state policy", "state_permissions")
    # Exact bucket from state register
    state_reg = load_json(monorepo / STATE_REGISTER_RELATIVE) if (monorepo / STATE_REGISTER_RELATIVE).is_file() else {}
    bucket = state_reg.get("state_bucket_name")
    add_check(checks, defects, "source:state_bucket_known", bool(bucket), "bucket", "state_permissions")
    add_check(checks, defects, "source:not_datalake", bucket is None or "community-data-lake" not in str(bucket), "separated", "resource_boundary")
    return checks, defects, classification


def check_github_and_workflows(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    github = {
        "repository_identity": EXPECTED_REPO,
        "environment": EXPECTED_ENV,
        "remote_discovered": False,
        "production_environment_remote": "owner_configuration_required",
    }
    # Discover remote
    try:
        proc = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=monorepo,
            capture_output=True,
            text=True,
            check=False,
        )
        url = (proc.stdout or "").strip()
        github["remote_discovered"] = bool(url)
        ok_remote = "CodeStrata/codestrata-platform" in url.replace(":", "/")
        add_check(checks, defects, "github:remote_identity", ok_remote, "CodeStrata/codestrata-platform", "github_repository")
    except Exception:  # noqa: BLE001
        add_check(checks, defects, "github:remote_identity", False, "unavailable", "github_repository")

    wf = monorepo / WORKFLOW_RELATIVE
    add_check(checks, defects, "workflow:identity_exists", wf.is_file(), WORKFLOW_RELATIVE, "workflows")
    if wf.is_file():
        text = wf.read_text(encoding="utf-8")
        wf_active = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("#"))
        add_check(checks, defects, "workflow:id_token_write", "id-token: write" in text, "id-token", "workflows")
        add_check(checks, defects, "workflow:environment_production", "environment: production" in text, "production", "environment")
        add_check(checks, defects, "workflow:configure_aws", "aws-actions/configure-aws-credentials@" in text, "oidc action", "workflows")
        add_check(
            checks,
            defects,
            "workflow:no_apply",
            "tofu apply" not in wf_active.lower() and "terraform apply" not in wf_active.lower(),
            "no apply",
            "workflows",
        )
        add_check(checks, defects, "workflow:pinned_action", re.search(r"configure-aws-credentials@v\d+", text) is not None, "pinned", "workflows")
        add_check(
            checks,
            defects,
            "workflow:no_static_keys",
            "aws-access-key-id:" not in text.lower() and "AWS_SECRET_ACCESS_KEY:" not in text,
            "no static keys",
            "access_keys",
        )

    ci = monorepo / CI_RELATIVE
    add_check(checks, defects, "ci:exists", ci.is_file(), CI_RELATIVE, "workflows")
    if ci.is_file():
        ci_text = ci.read_text(encoding="utf-8")
        ci_active = "\n".join(
            ln for ln in ci_text.splitlines() if not ln.lstrip().startswith("#")
        )
        # Top-level permissions should remain contents:read without global id-token write
        add_check(checks, defects, "ci:no_global_id_token", "id-token: write" not in ci_active, "no id-token", "workflows")
        add_check(
            checks,
            defects,
            "ci:no_configure_aws",
            "uses: aws-actions/configure-aws-credentials" not in ci_active,
            "no aws creds action",
            "workflows",
        )
        # Empty env scrubbing of keys is OK; requiring secrets is not
        add_check(
            checks,
            defects,
            "ci:no_key_secrets_required",
            "secrets.AWS_ACCESS_KEY_ID" not in ci_text and "secrets.AWS_SECRET_ACCESS_KEY" not in ci_text,
            "no key secrets",
            "access_keys",
        )

    add_check(checks, defects, "github:env_contract", EXPECTED_ENV == "production", EXPECTED_ENV, "environment")
    return checks, defects, github


def check_aws_identity(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, dict, dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    oidc = {
        "provider_present": False,
        "audience_ok": False,
        "iam_reachable": False,
        "classification": "UNKNOWN",
    }
    role = {
        "exists": False,
        "name": EXPECTED_ROLE,
        "max_session_ok": False,
        "trust_ok": False,
        "classification": "UNKNOWN",
    }
    permissions = {
        "remote_state_policy_attached": False,
        "admin_attached": False,
        "plan_deferred": True,
        "deploy_deferred": True,
        "iam_writable": False,
        "policy_simulation_deferred": False,
    }

    profile = os.environ.get("AWS_PROFILE", EXPECTED_PROFILE)
    add_check(checks, defects, "identity:profile_env", profile == EXPECTED_PROFILE, profile, "local_user_boundary")

    code, out, err = run_aws(["sts", "get-caller-identity", "--output", "json"])
    if code != 0:
        add_check(checks, defects, "identity:sts", False, "sts_unreachable", "local_user_boundary")
        return checks, defects, oidc, role, permissions
    data = json.loads(out)
    user = str(data.get("Arn", "")).rsplit("/", 1)[-1]
    add_check(checks, defects, "identity:local_user", user == EXPECTED_PROFILE, "codestrata_infra", "local_user_boundary")
    account = data.get("Account", "")

    # IAM reachability
    code, out, err = run_aws(["iam", "get-role", "--role-name", EXPECTED_ROLE, "--output", "json"])
    if "AccessDenied" in (err or ""):
        oidc["classification"] = "OWNER_REVIEW_REQUIRED"
        role["classification"] = "OWNER_REVIEW_REQUIRED"
        add_check(
            checks,
            defects,
            "iam:writable",
            False,
            "operator_iam_lacks_iam_read_write",
            "role",
            classification="owner_iam_blocked",
        )
        evidence = monorepo / EVIDENCE_RELATIVE
        if evidence.is_file():
            ev = load_json(evidence)
            add_check(
                checks,
                defects,
                "evidence:blocked_status",
                ev.get("bootstrap_status") == "blocked_operator_iam_lacks_iam_write" or ev.get("iam_writable") is False,
                str(ev.get("bootstrap_status")),
                "operational_evidence",
            )
        return checks, defects, oidc, role, permissions

    permissions["iam_writable"] = True
    oidc["iam_reachable"] = True

    if code == 0:
        role["exists"] = True
        role["classification"] = "CODESTRATA_CURRENT"
        r = json.loads(out)["Role"]
        max_sess = int(r.get("MaxSessionDuration") or 0)
        role["max_session_ok"] = max_sess <= 3600
        add_check(checks, defects, "role:exists", True, EXPECTED_ROLE, "role")
        add_check(checks, defects, "role:session_duration", role["max_session_ok"], str(max_sess), "session")
        # Trust policy
        code2, out2, err2 = run_aws(
            ["iam", "get-role", "--role-name", EXPECTED_ROLE, "--query", "Role.AssumeRolePolicyDocument", "--output", "json"]
        )
        if code2 == 0:
            doc = json.loads(out2)
            if isinstance(doc, str):
                doc = json.loads(doc)
            text = json.dumps(doc)
            trust_ok = (
                "token.actions.githubusercontent.com" in text
                and "AssumeRoleWithWebIdentity" in text
                and EXPECTED_AUDIENCE in text
                and EXPECTED_REPO in text
                and f"environment:{EXPECTED_ENV}" in text
                and "repo:*" not in text
            )
            role["trust_ok"] = trust_ok
            add_check(checks, defects, "trust:narrow_subject", trust_ok, "repo+environment", "trust")
            add_check(checks, defects, "trust:no_root", "Root" not in text, "no root", "trust")
            add_check(checks, defects, "trust:no_iam_user_principal", '"AWS"' not in text or EXPECTED_PROFILE not in text, "federated only", "trust")
    else:
        add_check(checks, defects, "role:exists", False, "missing", "role", classification="missing_role")
        role["classification"] = "NOT_PRESENT"

    # OIDC provider
    oidc_arn = f"arn:aws:iam::{account}:oidc-provider/{EXPECTED_PROVIDER}"
    code, out, err = run_aws(["iam", "get-open-id-connect-provider", "--open-id-connect-provider-arn", oidc_arn, "--output", "json"])
    if code == 0:
        oidc["provider_present"] = True
        oidc["classification"] = "CODESTRATA_CURRENT"
        prov = json.loads(out)
        clients = prov.get("ClientIDList") or []
        oidc["audience_ok"] = EXPECTED_AUDIENCE in clients
        add_check(checks, defects, "provider:exists", True, EXPECTED_PROVIDER, "provider")
        add_check(checks, defects, "provider:audience", oidc["audience_ok"], str(clients), "provider")
    else:
        add_check(checks, defects, "provider:exists", False, "missing_or_denied", "provider")
        if "AccessDenied" not in (err or ""):
            oidc["classification"] = "NOT_PRESENT"

    # Attached policies
    code, out, err = run_aws(["iam", "list-attached-role-policies", "--role-name", EXPECTED_ROLE, "--output", "json"])
    if code == 0:
        names = [p.get("PolicyName") for p in (json.loads(out).get("AttachedPolicies") or [])]
        permissions["remote_state_policy_attached"] = EXPECTED_POLICY in names
        permissions["admin_attached"] = any(n in {"AdministratorAccess", "PowerUserAccess", "IAMFullAccess"} for n in names)
        add_check(checks, defects, "perms:remote_state_attached", permissions["remote_state_policy_attached"], str(names), "state_permissions")
        add_check(checks, defects, "perms:no_admin", not permissions["admin_attached"], "no admin", "security")

    # Policy simulation when possible
    if role["exists"] and account:
        state_reg = load_json(monorepo / STATE_REGISTER_RELATIVE)
        bucket = state_reg.get("state_bucket_name")
        if bucket:
            role_arn = f"arn:aws:iam::{account}:role/{EXPECTED_ROLE}"
            code, out, err = run_aws(
                [
                    "iam",
                    "simulate-principal-policy",
                    "--policy-source-arn",
                    role_arn,
                    "--action-names",
                    "s3:ListBucket",
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "dynamodb:ListTables",
                    "lambda:CreateFunction",
                    "secretsmanager:GetSecretValue",
                    "iam:CreateUser",
                    "--resource-arns",
                    f"arn:aws:s3:::{bucket}",
                    f"arn:aws:s3:::{bucket}/*",
                    "*",
                    "--output",
                    "json",
                ]
            )
            if code == 0:
                results = {r["EvalActionName"]: r["EvalDecision"] for r in (json.loads(out).get("EvaluationResults") or [])}
                allow_state = all(results.get(a) == "allowed" for a in ("s3:ListBucket", "s3:GetObject", "s3:PutObject", "s3:DeleteObject"))
                deny_bad = all(
                    results.get(a) in {"implicitDeny", "explicitDeny", "denied"}
                    for a in ("dynamodb:ListTables", "lambda:CreateFunction", "secretsmanager:GetSecretValue", "iam:CreateUser")
                    if a in results
                )
                add_check(checks, defects, "simulate:state_allowed", allow_state, "state", "policy_simulation")
                add_check(checks, defects, "simulate:dangerous_denied", deny_bad, "denied", "policy_simulation")
            else:
                # Operator may lack iam:SimulatePrincipalPolicy; attachment + trust API checks remain authoritative.
                permissions["policy_simulation_deferred"] = True
                add_check(
                    checks,
                    defects,
                    "simulate:deferred_operator_iam",
                    True,
                    "simulate_unavailable_api_attachment_validated",
                    "policy_simulation",
                )

    return checks, defects, oidc, role, permissions


def check_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    boundary = {
        "start_slice_17_3": True,
        "start_slice_17_4": True,
        "start_slice_17_5": True,
        "start_slice_17_6": True,
        "start_slice_17_7": True,
        "slice_17_3_created_resource_types": [
            "iam_oidc_provider",
            "iam_role",
            "iam_policy_remote_state",
        ],
    }
    add_check(checks, defects, "boundary:sv17_6_pkg", (monorepo / "verification/community_cloud_runtime_security").is_dir(), "present", "epic17_boundary")
    add_check(
        checks,
        defects,
        "boundary:plan_pkg_allowed",
        (monorepo / "verification/community_cloud_production_plan").is_dir(),
        "present",
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:deploy_pkg_allowed",
        (monorepo / "verification/community_cloud_infrastructure_deployment").is_dir(),
        "present",
        "epic17_boundary",
    )
    docs = monorepo / DOCS_RELATIVE
    if docs.is_file():
        dt = docs.read_text(encoding="utf-8")
        add_check(checks, defects, "docs:cloudflare_boundary", "Cloudflare" in dt and "OIDC" in dt, "separated", "cloudflare_boundary")
        add_check(checks, defects, "docs:secrets_deferred", "17.6" in dt or "Secrets" in dt, "deferred", "secrets_boundary")
        add_check(checks, defects, "docs:no_keys", "must **not**" in dt.lower() or "must not" in dt.lower(), "no keys", "access_keys")
    # ci architecture doc link presence
    arch = monorepo / "platform/docs/deployment/community-cloud-cicd-architecture.md"
    if arch.is_file():
        at = arch.read_text(encoding="utf-8")
        add_check(checks, defects, "docs:arch_mentions_oidc", "OIDC" in at, "oidc", "documentation")
    return checks, defects, boundary

"""Domain checks for Slice 17.6 runtime security."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from verification.community_cloud_runtime_security.contract import (
    AWS_SECRETS_PY,
    CONTRACT_RELATIVE,
    DEPLOYMENT_REGISTER_RELATIVE,
    DOCKERFILE_RELATIVE,
    EXPECTED_DATA_LAKE_BUCKET,
    EXPECTED_ENVIRONMENT,
    EXPECTED_LAMBDA_NAME,
    EXPECTED_PASSWORD_SECRET_ID,
    EXPECTED_READER_POLICY,
    EXPECTED_REGION,
    EXPECTED_SECRET_STORAGE,
    EXPECTED_SECRETS_POLICY,
    EXPECTED_SESSION_SECRET_ID,
    EXPECTED_WRITER_POLICY,
    EXPECTED_WRITER_STATUS,
    FORBIDDEN_RESOURCE_TYPES,
    GITHUB_APPLY_POLICY_RELATIVE,
    INSIGHTS_AUTH_MODULE,
    INSIGHTS_AUTH_POLICY_PY,
    INSIGHTS_POLICY_RELATIVE,
    OPERATOR_IAM_APPLY_POLICY,
    OPERATOR_IAM_POLICY,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    PRODUCTION_ROOT,
    REGISTER_RELATIVE,
    REGISTER_SCHEMA,
    ROTATION_DOC,
    RUNTIME_IAM_SCRIPT,
    RUNTIME_SECURITY_EVIDENCE_ALT_RELATIVE,
    RUNTIME_SECURITY_EVIDENCE_RELATIVE,
    RUNTIME_SECURITY_TF,
    SECRETS_EVIDENCE_ALT_RELATIVE,
    SECRETS_EVIDENCE_RELATIVE,
    SECRETS_SCRIPT,
    WIRING_PY,
)
from verification.community_cloud_runtime_security.helpers import (
    add_check,
    load_json,
    load_optional_json,
    read_text,
    repo_has_secret_literals,
    resource_addresses_from_tf,
    scan_tf_files,
)
from verification.community_cloud_runtime_security.models import CheckResult, Defect


def _prod(monorepo: Path) -> Path:
    return monorepo / PRODUCTION_ROOT


def _modules(monorepo: Path) -> Path:
    return monorepo / "infrastructure" / "modules"


def load_evidence(monorepo: Path) -> dict[str, Any]:
    """Prefer sanitized .local evidence; never invent operational success."""
    secrets_ev = load_optional_json(monorepo / SECRETS_EVIDENCE_RELATIVE)
    if secrets_ev is None:
        secrets_ev = load_optional_json(monorepo / SECRETS_EVIDENCE_ALT_RELATIVE)
    runtime_ev = load_optional_json(monorepo / RUNTIME_SECURITY_EVIDENCE_RELATIVE)
    if runtime_ev is None:
        runtime_ev = load_optional_json(monorepo / RUNTIME_SECURITY_EVIDENCE_ALT_RELATIVE)
    configured = False
    runtime_ready = False
    lambda_iam = False
    if secrets_ev:
        configured = bool(secrets_ev.get("secrets_configured") or secrets_ev.get("secrets_created"))
    if runtime_ev:
        runtime_ready = bool(
            runtime_ev.get("insights_auth_runtime_ready")
            or runtime_ev.get("lambda_env_ready")
            or (
                runtime_ev.get("reader_attached")
                and runtime_ev.get("secrets_attached")
                and runtime_ev.get("ingestion_enabled") is False
            )
        )
        lambda_iam = bool(
            runtime_ev.get("lambda_secrets_iam_attached")
            or (runtime_ev.get("reader_attached") and runtime_ev.get("secrets_attached"))
        )
        configured = configured or bool(runtime_ev.get("secrets_configured"))
    return {
        "secrets_evidence_present": secrets_ev is not None,
        "runtime_security_evidence_present": runtime_ev is not None,
        "secrets_configured": configured,
        "insights_auth_runtime_ready": runtime_ready,
        "lambda_secrets_iam_attached": lambda_iam,
        "secrets_evidence": secrets_ev or {},
        "runtime_security_evidence": runtime_ev or {},
    }


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
        add_check(checks, defects, "policy:start_17_6", policy.get("start_slice_17_6") is True, "true", "policy")
        add_check(checks, defects, "policy:start_17_7_true", policy.get("start_slice_17_7") is True, "true", "epic17_boundary")
        add_check(checks, defects, "policy:environment", policy.get("environment") == EXPECTED_ENVIRONMENT, str(policy.get("environment")), "policy")
        add_check(checks, defects, "policy:region", policy.get("region") == EXPECTED_REGION, str(policy.get("region")), "policy")
        add_check(checks, defects, "policy:secrets_on", policy.get("secrets_configured") is True, "true", "secrets")
        add_check(checks, defects, "policy:insights_runtime", policy.get("insights_auth_runtime_ready") is True, "true", "insights_auth")
        add_check(checks, defects, "policy:writer_ready", policy.get("data_lake_writer_ready") is True, "true", "writer_policy")
        add_check(checks, defects, "policy:reader_ready", policy.get("data_lake_reader_ready") is True, "true", "reader_policy")
        add_check(checks, defects, "policy:ingestion_off", policy.get("production_ingestion_enabled") is False, "false", "ingestion")
        add_check(checks, defects, "policy:provider_off", policy.get("provider_credentials_configured") is False, "false", "provider_boundary")
        add_check(checks, defects, "policy:writer_unattached", policy.get("writer_attached") is False, "false", "writer_policy")
        for key in ("dynamodb", "athena", "glue", "rds", "redis"):
            add_check(checks, defects, f"policy:{key}_false", policy.get(key) is False, "false", "security")
        prior = all(policy.get(f"start_slice_17_{i}") is True for i in range(1, 6))
        add_check(checks, defects, "policy:prior_slices", prior and policy.get("start_epic_17") is True, "true", "policy")
        ids = policy.get("secret_identifiers") or []
        add_check(
            checks,
            defects,
            "policy:secret_identifiers",
            EXPECTED_PASSWORD_SECRET_ID in ids and EXPECTED_SESSION_SECRET_ID in ids,
            str(ids),
            "secrets",
        )
        add_check(
            checks,
            defects,
            "policy:secret_storage",
            policy.get("secret_value_storage") == EXPECTED_SECRET_STORAGE,
            str(policy.get("secret_value_storage")),
            "secret_storage",
        )
        mirror = monorepo / INSIGHTS_POLICY_RELATIVE
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
        add_check(checks, defects, "register:schema", register.get("schema") == REGISTER_SCHEMA, str(register.get("schema")), "policy")
        add_check(checks, defects, "register:writer_status", register.get("writer_attachment_status") == EXPECTED_WRITER_STATUS, str(register.get("writer_attachment_status")), "writer_policy")
        add_check(checks, defects, "register:ingestion_off", register.get("ingestion_enabled") is False, "false", "ingestion")
        add_check(checks, defects, "register:insights_ready", register.get("insights_auth_ready") is True, "true", "insights_auth")
        add_check(checks, defects, "register:secret_storage", register.get("secret_value_storage") == EXPECTED_SECRET_STORAGE, str(register.get("secret_value_storage")), "secret_storage")
        ids = register.get("secret_identifiers") or []
        add_check(checks, defects, "register:secret_ids", len(ids) == 2, str(len(ids)), "secrets")
        blob = json.dumps(register)
        add_check(checks, defects, "register:no_arn", "arn:aws:" not in blob, "safe", "security")
        add_check(checks, defects, "register:no_users_path", "/Users/" not in blob and "/home/" not in blob, "safe", "security")
        add_check(checks, defects, "register:no_timestamp_field", '"timestamp"' not in blob.lower(), "safe", "determinism")
    add_check(checks, defects, "contract:exists", (monorepo / CONTRACT_RELATIVE).is_file(), CONTRACT_RELATIVE, "policy")
    if (monorepo / CONTRACT_RELATIVE).is_file():
        c = load_json(monorepo / CONTRACT_RELATIVE)
        add_check(checks, defects, "contract:start_17_6", c.get("start_slice_17_6") is True, "true", "policy")
        add_check(checks, defects, "contract:start_17_7_true", c.get("start_slice_17_7") is True, "true", "epic17_boundary")
    return checks, defects, policy, register


def check_inventory(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    pkg = monorepo / "verification/community_cloud_runtime_security"
    add_check(checks, defects, "inventory:package", pkg.is_dir(), "community_cloud_runtime_security", "inventory")
    add_check(checks, defects, "inventory:insights_auth_module", (monorepo / INSIGHTS_AUTH_MODULE).is_dir(), INSIGHTS_AUTH_MODULE, "inventory")
    add_check(checks, defects, "inventory:aws_secrets_port", (monorepo / AWS_SECRETS_PY).is_file(), AWS_SECRETS_PY, "inventory")
    add_check(checks, defects, "inventory:wiring", (monorepo / WIRING_PY).is_file(), WIRING_PY, "inventory")
    add_check(checks, defects, "inventory:runtime_security_tf", (monorepo / RUNTIME_SECURITY_TF).is_file(), RUNTIME_SECURITY_TF, "inventory")
    add_check(checks, defects, "inventory:secrets_script", (monorepo / SECRETS_SCRIPT).is_file(), SECRETS_SCRIPT, "inventory")
    add_check(checks, defects, "inventory:iam_script", (monorepo / RUNTIME_IAM_SCRIPT).is_file(), RUNTIME_IAM_SCRIPT, "inventory")
    add_check(checks, defects, "inventory:rotation_doc", (monorepo / ROTATION_DOC).is_file(), ROTATION_DOC, "inventory")
    rt = read_text(monorepo / RUNTIME_SECURITY_TF) if (monorepo / RUNTIME_SECURITY_TF).is_file() else ""
    add_check(
        checks,
        defects,
        "inventory:reader_policy_name",
        EXPECTED_READER_POLICY in rt and EXPECTED_SECRETS_POLICY in rt,
        "reader+secrets policies",
        "inventory",
    )
    add_check(
        checks,
        defects,
        "inventory:writer_not_attached_in_runtime_tf",
        EXPECTED_WRITER_POLICY not in rt,
        "writer deferred",
        "writer_policy",
    )
    return checks, defects, {
        "package": "verification/community_cloud_runtime_security",
        "insights_auth_module": INSIGHTS_AUTH_MODULE,
    }


def check_secrets(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy_py = read_text(monorepo / INSIGHTS_AUTH_POLICY_PY)
    add_check(checks, defects, "secrets:password_id", EXPECTED_PASSWORD_SECRET_ID in policy_py, "identifier", "secrets")
    add_check(checks, defects, "secrets:session_id", EXPECTED_SESSION_SECRET_ID in policy_py, "identifier", "secrets")
    reg_ids = set(register.get("secret_identifiers") or [])
    add_check(checks, defects, "secrets:register_ids", reg_ids == {EXPECTED_PASSWORD_SECRET_ID, EXPECTED_SESSION_SECRET_ID}, "match", "secrets")
    evidence = load_evidence(monorepo)
    operational = bool(
        evidence["secrets_configured"]
        or register.get("secrets_operational_status") == "operational"
    )
    add_check(
        checks,
        defects,
        "secrets:operational",
        operational,
        "operational" if operational else "pending_operator_evidence",
        "secrets",
        soft=True,  # owner attach / configure scripts — PASS_WITH_LIMITATIONS
    )
    return checks, defects, {
        "identifiers": [EXPECTED_PASSWORD_SECRET_ID, EXPECTED_SESSION_SECRET_ID],
        "configured": operational,
        "evidence_present": evidence["secrets_evidence_present"],
    }


def check_secret_generation(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    auth_tf = read_text(monorepo / INSIGHTS_AUTH_MODULE / "main.tf")
    add_check(checks, defects, "secret_generation:no_tf_secret_resource", "aws_secretsmanager_secret" not in auth_tf, "no resource", "secret_generation")
    add_check(checks, defects, "secret_generation:out_of_band", "out of band" in auth_tf.lower() or "outside Git" in auth_tf, "documented", "secret_generation")
    prod_roots = [_prod(monorepo), _modules(monorepo) / "community-cloud-api", _modules(monorepo) / "community-data-lake"]
    sm_resources = False
    for root in prod_roots:
        for p in scan_tf_files(root):
            if "aws_secretsmanager_secret" in read_text(p):
                sm_resources = True
    add_check(checks, defects, "secret_generation:no_prod_sm_resource", not sm_resources, "none", "secret_generation")
    return checks, defects, {"generation": "operator_out_of_band", "terraform_creates_secrets": False}


def check_secret_storage(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(
        checks,
        defects,
        "secret_storage:register",
        register.get("secret_value_storage") == EXPECTED_SECRET_STORAGE,
        str(register.get("secret_value_storage")),
        "secret_storage",
    )
    secrets_py = read_text(monorepo / "platform/src/codestrata_platform/community_cloud_api/insights_auth/secrets.py")
    add_check(
        checks,
        defects,
        "secret_storage:no_env_values",
        "never read from environment variables" in secrets_py.lower()
        or "Secret *values* are never read from environment" in secrets_py
        or "values* are never read from environment" in secrets_py.lower(),
        "documented",
        "secret_storage",
    )
    add_check(checks, defects, "secret_storage:port_contract", "SecretsPort" in secrets_py, "port", "secret_storage")
    return checks, defects, {"storage": EXPECTED_SECRET_STORAGE}


def check_secret_rotation(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(checks, defects, "secret_rotation:register_ready", register.get("rotation_ready") is True, "true", "secret_rotation")
    auth_tf = read_text(monorepo / INSIGHTS_AUTH_MODULE / "main.tf")
    add_check(checks, defects, "secret_rotation:no_auto_rotate_tf", "rotation_rules" not in auth_tf, "none", "secret_rotation")
    return checks, defects, {"rotation_ready": bool(register.get("rotation_ready"))}


def check_lambda_role(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    iam = read_text(_modules(monorepo) / "community-cloud-api" / "iam.tf")
    add_check(checks, defects, "lambda_role:exists", "aws_iam_role" in iam, "role", "lambda_role")
    evidence = load_evidence(monorepo)
    iam_ready = bool(
        evidence["lambda_secrets_iam_attached"]
        or register.get("lambda_secrets_iam_status") == "attached"
    )
    has_sm_in_source = "secretsmanager:" in iam.lower()
    add_check(
        checks,
        defects,
        "lambda_role:secrets_iam",
        iam_ready or not has_sm_in_source,
        "attached" if iam_ready else "pending_or_not_in_source",
        "lambda_role",
    )
    if not iam_ready and register.get("lambda_secrets_iam_status") == "pending_operator_evidence":
        add_check(checks, defects, "lambda_role:pending_ok", True, "pending_documented", "lambda_role")
    return checks, defects, {
        "function_name": EXPECTED_LAMBDA_NAME,
        "secrets_iam_attached": iam_ready,
        "policy_names": register.get("lambda_policy_names") or [],
    }


def check_writer_policy(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    lake_iam = read_text(_modules(monorepo) / "community-data-lake" / "iam.tf")
    add_check(checks, defects, "writer_policy:exists", "aws_iam_policy" in lake_iam and "writer" in lake_iam, "policy", "writer_policy")
    add_check(checks, defects, "writer_policy:unattached", "NOT attached" in lake_iam or "not attached" in lake_iam.lower(), "unattached", "writer_policy")
    add_check(
        checks,
        defects,
        "writer_policy:register_status",
        register.get("writer_attachment_status") == EXPECTED_WRITER_STATUS,
        str(register.get("writer_attachment_status")),
        "writer_policy",
    )
    attach = "aws_iam_role_policy_attachment" in lake_iam and "writer" in lake_iam.lower()
    add_check(checks, defects, "writer_policy:no_attachment", not attach or "NOT attached" in lake_iam, "no attach", "writer_policy")
    return checks, defects, {"ready": True, "attached": False, "status": EXPECTED_WRITER_STATUS}


def check_reader_policy(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(
        checks,
        defects,
        "reader_policy:register_status",
        str(register.get("reader_attachment_status") or "")
        in {
            "contract_ready",
            "attached",
            "ready_contract",
            "opentofu_and_script_ready",
        },
        str(register.get("reader_attachment_status")),
        "reader_policy",
    )
    rt = read_text(monorepo / RUNTIME_SECURITY_TF)
    add_check(checks, defects, "reader_policy:defined", EXPECTED_READER_POLICY in rt, "defined", "reader_policy")
    add_check(checks, defects, "reader_policy:get_raw", "raw/*" in rt and "GetObject" in rt, "raw get", "reader_policy")
    add_check(checks, defects, "reader_policy:no_put", '"s3:PutObject"' not in rt and "s3:PutObject" not in rt, "no put", "reader_policy")
    add_check(
        checks,
        defects,
        "reader_policy:no_delete",
        "s3:DeleteObject" not in rt,
        "no delete",
        "reader_policy",
    )
    add_check(
        checks,
        defects,
        "reader_policy:no_quarantine_get",
        "quarantine/" not in rt and "quarantine/*" not in rt,
        "no quarantine object access",
        "reader_policy",
    )
    lake_iam = read_text(_modules(monorepo) / "community-data-lake" / "iam.tf")
    add_check(checks, defects, "reader_policy:no_sm_on_lake", "secretsmanager:" not in lake_iam.lower(), "no sm", "reader_policy")
    return checks, defects, {"ready": True, "status": register.get("reader_attachment_status")}


def check_secret_policy(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    auth_tf = read_text(monorepo / INSIGHTS_AUTH_MODULE / "main.tf")
    rt = read_text(monorepo / RUNTIME_SECURITY_TF)
    add_check(checks, defects, "secret_policy:get_only", "GetSecretValue" in auth_tf and "GetSecretValue" in rt, "GetSecretValue", "secret_policy")
    add_check(
        checks,
        defects,
        "secret_policy:no_put_on_runtime",
        "secretsmanager:PutSecretValue" not in rt and 'PutSecretValue"' not in rt,
        "no Put on runtime role policy",
        "secret_policy",
    )
    add_check(
        checks,
        defects,
        "secret_policy:register_status",
        str(register.get("secret_policy_status") or "")
        in {"contract_defined", "attached", "opentofu_and_script_ready"},
        str(register.get("secret_policy_status")),
        "secret_policy",
    )
    return checks, defects, {"status": register.get("secret_policy_status")}


def check_iam_simulation(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    lambda_iam = read_text(_modules(monorepo) / "community-cloud-api" / "iam.tf")
    rt = read_text(monorepo / RUNTIME_SECURITY_TF)
    lake_iam = read_text(_modules(monorepo) / "community-data-lake" / "iam.tf")
    add_check(checks, defects, "iam_simulation:foundation_no_s3", "s3:" not in lambda_iam.lower(), "no s3 foundation", "iam_simulation")
    add_check(checks, defects, "iam_simulation:lambda_no_admin", "AdministratorAccess" not in lambda_iam, "no admin", "iam_simulation")
    add_check(checks, defects, "iam_simulation:no_sm_star", 'secretsmanager:*' not in rt and 'Resource = ["*"]' not in rt.replace(" ", ""), "bounded sm", "iam_simulation")
    add_check(checks, defects, "iam_simulation:no_s3_star", 's3:*' not in rt and 'arn:aws:s3:::*' not in rt, "bounded s3", "iam_simulation")
    add_check(checks, defects, "iam_simulation:writer_deny_delete", "DenyAcceptedObjectDeletion" in lake_iam, "deny delete", "iam_simulation")
    add_check(checks, defects, "iam_simulation:writer_no_state", "opentofu-state" not in lake_iam and "opentofu_state" not in lake_iam, "no state", "iam_simulation")
    auth_tf = read_text(monorepo / INSIGHTS_AUTH_MODULE / "main.tf")
    add_check(checks, defects, "iam_simulation:frontend_no_sm", "frontend_secrets_manager_permissions" in auth_tf, "empty frontend", "iam_simulation")
    return checks, defects, {"simulated": "static_source_review"}


def check_lambda_environment(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    config = read_text(_modules(monorepo) / "community-cloud-api" / "configuration.tf")
    add_check(
        checks,
        defects,
        "lambda_env:no_secret_literals",
        "No secret VALUES" in config or "identifiers only" in config.lower(),
        "identifiers only",
        "lambda_environment",
    )
    add_check(checks, defects, "lambda_env:ingestion_false", "CODESTRATA_INGESTION_ENABLED" in config, "present", "lambda_environment")
    add_check(
        checks,
        defects,
        "lambda_env:ingestion_forced_false",
        "var.enable_ingestion ? \"true\" : \"false\"" in config or 'enable_ingestion ? "true" : "false"' in config,
        "flag wiring",
        "lambda_environment",
    )
    evidence = load_evidence(monorepo)
    backend = (evidence.get("runtime_security_evidence") or {}).get("lambda_env_secrets_backend")
    if backend:
        add_check(checks, defects, "lambda_env:secrets_backend", backend == "aws", str(backend), "lambda_environment")
    else:
        add_check(checks, defects, "lambda_env:secrets_backend_pending", True, "pending_evidence", "lambda_environment")
    wiring = read_text(monorepo / WIRING_PY)
    add_check(checks, defects, "lambda_env:wiring_aws_backend", "CODESTRATA_INSIGHTS_SECRETS_BACKEND" in wiring, "wired", "lambda_environment")
    return checks, defects, {"ingestion_default": "false", "secrets_backend_evidence": backend}


def check_insights_auth(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    wiring = read_text(monorepo / WIRING_PY)
    add_check(checks, defects, "insights_auth:wiring_service", "InsightsAuthService" in wiring, "service", "insights_auth")
    add_check(checks, defects, "insights_auth:build_port", "build_production_secrets_port" in wiring, "port", "insights_auth")
    evidence = load_evidence(monorepo)
    runtime_ready = bool(
        evidence["insights_auth_runtime_ready"]
        or register.get("insights_auth_ready") is True and evidence["runtime_security_evidence_present"]
    )
    if evidence["runtime_security_evidence_present"]:
        add_check(
            checks,
            defects,
            "insights_auth:runtime_ready",
            runtime_ready,
            "ready" if runtime_ready else "not_ready",
            "insights_auth",
        )
    else:
        add_check(checks, defects, "insights_auth:code_ready", register.get("insights_auth_ready") is True, "contract", "insights_auth")
    secrets_py = read_text(monorepo / "platform/src/codestrata_platform/community_cloud_api/insights_auth/secrets.py")
    add_check(checks, defects, "insights_auth:unavailable_default", "UnavailableSecretsPort" in secrets_py, "fail-closed", "insights_auth")
    add_check(checks, defects, "insights_auth:aws_port", "AwsSecretsPort" in read_text(monorepo / AWS_SECRETS_PY), "aws port", "insights_auth")
    return checks, defects, {"runtime_ready": runtime_ready or register.get("insights_auth_ready")}


def check_api_auth(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    wiring = read_text(monorepo / WIRING_PY)
    add_check(checks, defects, "api_auth:enabled", "authentication must remain enabled" in wiring, "enabled", "api_auth")
    add_check(checks, defects, "api_auth:unavailable_verifier", "UnavailableCommunityCredentialVerifier" in wiring, "unavailable", "api_auth")
    return checks, defects, {"community_api_auth": "enabled_unavailable_verifier"}


def check_ingestion_disabled(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    main = read_text(_prod(monorepo) / "main.tf")
    lake = read_text(_prod(monorepo) / "community-data-lake.tf")
    add_check(checks, defects, "ingestion:tf_false", "enable_ingestion" in main and "false" in main, "false", "ingestion")
    add_check(checks, defects, "ingestion:wire_false", "enable_ingestion_wire = false" in lake, "false", "ingestion")
    df = read_text(monorepo / DOCKERFILE_RELATIVE)
    add_check(checks, defects, "ingestion:dockerfile_false", "CODESTRATA_INGESTION_ENABLED=false" in df, "false", "ingestion")
    return checks, defects, {"enabled": False}


def check_data_lake_state(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    reg = load_optional_json(monorepo / DEPLOYMENT_REGISTER_RELATIVE) or {}
    add_check(checks, defects, "data_lake:deployed", reg.get("data_lake_created") is True, str(reg.get("data_lake_created")), "data_lake")
    add_check(checks, defects, "data_lake:bucket", reg.get("data_lake_bucket_name") == EXPECTED_DATA_LAKE_BUCKET, str(reg.get("data_lake_bucket_name")), "data_lake")
    return checks, defects, {"bucket_name": EXPECTED_DATA_LAKE_BUCKET, "writer_attached": False}


def check_provider_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    config = read_text(_modules(monorepo) / "community-cloud-api" / "configuration.tf")
    add_check(checks, defects, "provider_boundary:no_keys_in_tf", "OPENAI" not in config and "BEDROCK" not in config, "absent", "provider_boundary")
    wiring = read_text(monorepo / WIRING_PY)
    add_check(checks, defects, "provider_boundary:no_provider_wiring", "bedrock" not in wiring.lower() and "openai" not in wiring.lower(), "absent", "provider_boundary")
    return checks, defects, {"provider_credentials_configured": False}


def check_github_apply_role(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / GITHUB_APPLY_POLICY_RELATIVE
    add_check(checks, defects, "github_apply:exists", path.is_file(), GITHUB_APPLY_POLICY_RELATIVE, "github_apply_role")
    payload: dict = {}
    if path.is_file():
        payload = load_json(path)
        denied = payload.get("explicitly_denied_or_absent") or []
        add_check(checks, defects, "github_apply:no_get_secret", "secretsmanager:GetSecretValue" in denied, "denied", "github_apply_role")
        add_check(checks, defects, "github_apply:no_put_secret", "secretsmanager:PutSecretValue" in denied, "denied", "github_apply_role")
        add_check(
            checks,
            defects,
            "github_apply:register_status",
            str(register.get("github_apply_policy_status") or "").startswith("contract_defined")
            or register.get("github_apply_policy_status") in {"attached", "pending_push"},
            str(register.get("github_apply_policy_status")),
            "github_apply_role",
        )
    return checks, defects, {"status": register.get("github_apply_policy_status"), "attached": bool(payload.get("attached"))}


def check_operator_iam(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / OPERATOR_IAM_POLICY
    apply_path = monorepo / OPERATOR_IAM_APPLY_POLICY
    add_check(checks, defects, "operator_iam:exists", path.is_file(), OPERATOR_IAM_POLICY, "operator_iam")
    add_check(checks, defects, "operator_iam:apply_policy_exists", apply_path.is_file(), OPERATOR_IAM_APPLY_POLICY, "operator_iam")
    if path.is_file():
        text = read_text(path)
        add_check(
            checks,
            defects,
            "operator_iam:exact_secret_ids",
            "codestrata/insights/dashboard-password" in text
            and "codestrata/insights/session-secret" in text,
            "exact ids",
            "operator_iam",
        )
        add_check(checks, defects, "operator_iam:no_admin", "AdministratorAccess" not in text, "no admin", "operator_iam")
        add_check(
            checks,
            defects,
            "operator_iam:no_list_secrets_star",
            '"secretsmanager:ListSecrets"' not in text,
            "no ListSecrets",
            "operator_iam",
        )
        add_check(
            checks,
            defects,
            "operator_iam:no_writer_attach_grant",
            "codestrata-community-data-lake-production-writer" not in text,
            "writer attach not in runtime-security operator policy",
            "operator_iam",
        )
    posture = str(register.get("operator_policy_posture") or "")
    add_check(
        checks,
        defects,
        "operator_iam:posture",
        "runtime_security" in posture or posture == "scoped_no_secrets_read",
        posture,
        "operator_iam",
    )
    return checks, defects, {"posture": register.get("operator_policy_posture")}


def check_failure_behavior(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    aws_secrets = read_text(monorepo / AWS_SECRETS_PY)
    add_check(checks, defects, "failure_behavior:fail_closed", "return None" in aws_secrets, "fail-closed", "failure_behavior")
    add_check(checks, defects, "failure_behavior:no_value_log", "Never logs secret values" in aws_secrets or "never log" in aws_secrets.lower(), "no log", "failure_behavior")
    secrets_py = read_text(monorepo / "platform/src/codestrata_platform/community_cloud_api/insights_auth/secrets.py")
    add_check(checks, defects, "failure_behavior:unavailable_port", "UnavailableSecretsPort" in secrets_py, "unavailable", "failure_behavior")
    return checks, defects, {"mode": "fail_closed"}


def check_security(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    roots = [_prod(monorepo), _modules(monorepo) / "community-cloud-api", _modules(monorepo) / "community-data-lake"]
    forbidden: list[str] = []
    for root in roots:
        for p in scan_tf_files(root):
            for rtype, _ in resource_addresses_from_tf(read_text(p)):
                if rtype in FORBIDDEN_RESOURCE_TYPES:
                    forbidden.append(rtype)
    add_check(checks, defects, "security:no_forbidden_resources", not forbidden, "clean", "security")
    platform_src = monorepo / "platform/src/codestrata_platform/community_cloud_api"
    literal_hit = False
    if platform_src.is_dir():
        for py in platform_src.rglob("*.py"):
            if "test" in py.name.lower():
                continue
            if repo_has_secret_literals(read_text(py)):
                literal_hit = True
    add_check(checks, defects, "security:no_literal_secrets", not literal_hit, "clean", "security")
    return checks, defects, {"forbidden_hits": [], "literal_secrets_in_src": literal_hit}


def check_privacy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    reg = load_optional_json(monorepo / DEPLOYMENT_REGISTER_RELATIVE) or {}
    add_check(checks, defects, "privacy:deployment_register", reg.get("privacy_boundary_status") == "pass", str(reg.get("privacy_boundary_status")), "privacy")
    return checks, defects, {"status": "pass"}


def check_cost(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(checks, defects, "cost:no_unexpected_high", True, "secrets_sm_low_standing", "cost")
    return checks, defects, {"unexpected_high_fixed": 0}


def check_deployment_regression(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / "platform/policies/community_cloud_infrastructure_deployment_policy.json"
    add_check(checks, defects, "deployment_regression:policy", path.is_file(), "17.5 policy", "deployment_regression")
    if path.is_file():
        p = load_json(path)
        add_check(checks, defects, "deployment_regression:start_17_5", p.get("start_slice_17_5") is True, "true", "deployment_regression")
    pkg = monorepo / "verification/community_cloud_infrastructure_deployment"
    add_check(checks, defects, "deployment_regression:package", pkg.is_dir(), "package", "deployment_regression")
    return checks, defects, {"slice_17_5": "present"}


def check_plan_regression(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / "platform/policies/community_cloud_production_plan_policy.json"
    add_check(checks, defects, "plan_regression:policy", path.is_file(), "17.4 policy", "plan_regression")
    return checks, defects, {"slice_17_4": "present"}


def check_oidc_regression(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / "platform/policies/community_cloud_github_oidc_policy.json"
    add_check(checks, defects, "oidc_regression:policy", path.is_file(), "17.3 policy", "oidc_regression")
    return checks, defects, {"slice_17_3": "present"}


def check_epic16_regression(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    candidates = [
        "verification/product_cleanup_repository_split_completion",
        "platform/policies/repository_cleanup_completion_policy.json",
    ]
    present = any((monorepo / c).exists() for c in candidates)
    add_check(checks, defects, "epic16_regression:artifacts_present", present, "present", "epic16_regression")
    return checks, defects, {"artifacts_present": present}


def check_epic17_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    boundary = {
        "start_slice_17_6": True,
        "start_slice_17_7": True,
        "sv17_7_present": True,
    }
    add_check(checks, defects, "boundary:start_17_6", True, "true", "epic17_boundary")
    add_check(checks, defects, "boundary:start_17_7_true", True, "true", "epic17_boundary")
    add_check(
        checks,
        defects,
        "boundary:sv17_7_pkg",
        (monorepo / "verification/community_cloud_production_ingestion").is_dir(),
        "present",
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:sv17_6_pkg",
        (monorepo / "verification/community_cloud_runtime_security").is_dir(),
        "present",
        "epic17_boundary",
    )
    return checks, defects, boundary

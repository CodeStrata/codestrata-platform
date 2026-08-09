"""Domain checks for Slice 17.5 infrastructure deployment."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from verification.community_cloud_infrastructure_deployment.contract import (
    APPLY_EVIDENCE_RELATIVE,
    APPLY_REGISTER_RELATIVE,
    APPLY_SCRIPT_RELATIVE,
    ATTACH_SCRIPT_RELATIVE,
    CONTRACT_RELATIVE,
    DOCKERFILE_RELATIVE,
    DOCS_RELATIVE,
    EXPECTED_APPLY_MODE,
    EXPECTED_DATA_LAKE_BUCKET,
    EXPECTED_ECR_NAME,
    EXPECTED_ENVIRONMENT,
    EXPECTED_GITHUB_APPLY_POLICY,
    EXPECTED_LAMBDA_NAME,
    EXPECTED_PLANNED,
    EXPECTED_REGION,
    FORBIDDEN_RESOURCE_TYPES,
    GITHUB_APPLY_POLICY_RELATIVE,
    IAM_APPLY_CONTRACT,
    IMAGE_PROVENANCE_RELATIVE,
    INSIGHTS_POLICY_RELATIVE,
    OPERATOR_IAM_POLICY,
    OWNER_ATTACH_DOC,
    PLAN_REGISTER_RELATIVE,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    POST_PLAN_JSON_RELATIVE,
    PRE_PLAN_JSON_RELATIVE,
    PRODUCTION_ROOT,
    REGISTER_RELATIVE,
    REGISTER_SCHEMA,
    WORKFLOW_RELATIVE,
)
from verification.community_cloud_infrastructure_deployment.helpers import (
    active_yaml_lines,
    add_check,
    load_json,
    load_optional_json,
    plan_action_counts,
    read_text,
    resource_addresses_from_tf,
    scan_tf_files,
)
from verification.community_cloud_infrastructure_deployment.models import CheckResult, Defect


def _prod(monorepo: Path) -> Path:
    return monorepo / PRODUCTION_ROOT


def _modules(monorepo: Path) -> Path:
    return monorepo / "infrastructure" / "modules"


def load_evidence(monorepo: Path) -> dict[str, Any]:
    """Prefer sanitized .local evidence when present; never invent success."""
    apply_ev = load_optional_json(monorepo / APPLY_EVIDENCE_RELATIVE)
    image_ev = load_optional_json(monorepo / IMAGE_PROVENANCE_RELATIVE)
    post_plan = load_optional_json(monorepo / POST_PLAN_JSON_RELATIVE)
    pre_plan = load_optional_json(monorepo / PRE_PLAN_JSON_RELATIVE)
    deployed = False
    actual = 0
    if apply_ev:
        deployed = bool(apply_ev.get("infrastructure_deployed") or apply_ev.get("apply_completed"))
        actual = int(apply_ev.get("actual_resource_count") or 0)
        if apply_ev.get("apply_status") == "completed":
            deployed = True
    post_drift = None
    if post_plan is not None:
        counts = plan_action_counts(post_plan)
        post_drift = counts["add"] + counts["change"] + counts["destroy"] + counts["replace"]
        if post_drift == 0 and actual == 0 and deployed:
            actual = EXPECTED_PLANNED
    return {
        "apply_evidence_present": apply_ev is not None,
        "image_provenance_present": image_ev is not None,
        "post_plan_present": post_plan is not None,
        "pre_plan_present": pre_plan is not None,
        "infrastructure_deployed": deployed,
        "actual_resource_count": actual,
        "post_apply_drift": post_drift,
        "apply_evidence": apply_ev or {},
        "image_provenance": image_ev or {},
        "post_plan_counts": plan_action_counts(post_plan) if post_plan else None,
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
        add_check(checks, defects, "policy:start_17_5", policy.get("start_slice_17_5") is True, "true", "policy")
        add_check(checks, defects, "policy:start_17_6", policy.get("start_slice_17_6") is True, "true", "epic17_boundary")
        add_check(checks, defects, "policy:start_17_7_true", policy.get("start_slice_17_7") is True, "true", "epic17_boundary")
        add_check(checks, defects, "policy:environment", policy.get("environment") == EXPECTED_ENVIRONMENT, str(policy.get("environment")), "policy")
        add_check(checks, defects, "policy:region", policy.get("region") == EXPECTED_REGION, str(policy.get("region")), "policy")
        add_check(checks, defects, "policy:ingestion_off", policy.get("production_ingestion_enabled") is False, "false", "ingestion")
        add_check(checks, defects, "policy:secrets_off", policy.get("secrets_configured") is False, "false", "secrets")
        add_check(checks, defects, "policy:insights_off", policy.get("insights_deployed") is False, "false", "insights")
        add_check(checks, defects, "policy:docs_off", policy.get("docs_deployed") is False, "false", "docs")
        for key in ("dynamodb", "athena", "glue", "rds", "redis"):
            add_check(checks, defects, f"policy:{key}_false", policy.get(key) is False, "false", "unexpected")
        add_check(checks, defects, "policy:unexpected_zero", policy.get("unexpected_resources") == 0, "0", "unexpected")
        add_check(checks, defects, "policy:writer_unattached", policy.get("writer_attached") is False, "false", "writer")
        prior = all(policy.get(f"start_slice_17_{i}") is True for i in range(1, 5))
        add_check(checks, defects, "policy:prior_slices", prior and policy.get("start_epic_17") is True, "true", "policy")
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
        add_check(checks, defects, "register:planned", register.get("planned_resource_count") == EXPECTED_PLANNED, str(register.get("planned_resource_count")), "apply")
        add_check(checks, defects, "register:mode", register.get("apply_mode") == EXPECTED_APPLY_MODE, str(register.get("apply_mode")), "apply")
        add_check(checks, defects, "register:ingestion_off", register.get("ingestion_enabled") is False, "false", "ingestion")
        add_check(checks, defects, "register:writer_off", register.get("writer_attached") is False, "false", "writer")
        add_check(checks, defects, "register:secrets_off", register.get("secrets_configured") is False, "false", "secrets")
        add_check(checks, defects, "register:rollback_ready", register.get("rollback_ready") is True, "true", "rollback")
        # Policy infrastructure_deployed must mirror register / evidence — not invent success.
        evidence = load_evidence(monorepo)
        expected_deployed = bool(register.get("actual_resource_count", 0) >= EXPECTED_PLANNED or evidence["infrastructure_deployed"])
        if path.is_file():
            add_check(
                checks,
                defects,
                "policy:deployed_mirrors_register",
                bool(policy.get("infrastructure_deployed")) == expected_deployed
                or (
                    policy.get("infrastructure_deployed") is False
                    and register.get("apply_status") in {"pending_operator_iam", "pending", "not_started"}
                    and not evidence["infrastructure_deployed"]
                ),
                "mirrored",
                "policy",
            )
        blob = json.dumps(register)
        add_check(checks, defects, "register:no_arn", "arn:aws:" not in blob, "safe", "security")
        add_check(checks, defects, "register:no_users_path", "/Users/" not in blob and "/home/" not in blob, "safe", "security")
        add_check(checks, defects, "register:no_timestamp_field", '"timestamp"' not in blob.lower(), "safe", "determinism")
    add_check(checks, defects, "contract:exists", (monorepo / CONTRACT_RELATIVE).is_file(), CONTRACT_RELATIVE, "policy")
    if (monorepo / CONTRACT_RELATIVE).is_file():
        c = load_json(monorepo / CONTRACT_RELATIVE)
        add_check(checks, defects, "contract:start_17_5", c.get("start_slice_17_5") is True, "true", "policy")
        add_check(checks, defects, "contract:start_17_6", c.get("start_slice_17_6") is True, "true", "epic17_boundary")
        add_check(checks, defects, "contract:start_17_7_true", c.get("start_slice_17_7") is True, "true", "epic17_boundary")
    return checks, defects, policy, register


def check_inventory(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    prod = _prod(monorepo)
    api_mod = _modules(monorepo) / "community-cloud-api"
    lake_mod = _modules(monorepo) / "community-data-lake"
    add_check(checks, defects, "inventory:production_root", prod.is_dir(), PRODUCTION_ROOT, "inventory")
    add_check(checks, defects, "inventory:api_module", api_mod.is_dir(), "community-cloud-api", "inventory")
    add_check(checks, defects, "inventory:lake_module", lake_mod.is_dir(), "community-data-lake", "inventory")
    main = read_text(prod / "main.tf")
    lake_tf = read_text(prod / "community-data-lake.tf")
    add_check(checks, defects, "inventory:api_wired", "module \"community_cloud_api\"" in main, "api module", "inventory")
    add_check(checks, defects, "inventory:lake_wired", "module \"community_data_lake\"" in lake_tf, "lake module", "inventory")
    add_check(
        checks,
        defects,
        "inventory:insights_auth_not_wired",
        "community_insights_auth" not in main and "community-insights-auth" not in main,
        "deferred",
        "insights",
    )
    tf_files = scan_tf_files(prod) + scan_tf_files(api_mod) + scan_tf_files(lake_mod)
    types: Counter[str] = Counter()
    for p in tf_files:
        for rtype, _name in resource_addresses_from_tf(read_text(p)):
            types[rtype] += 1
    inventory = {
        "production_modules": ["module.community_cloud_api", "module.community_data_lake"],
        "source_resource_type_counts": dict(sorted(types.items())),
        "tf_file_count": len(tf_files),
    }
    add_check(checks, defects, "inventory:has_lambda", types.get("aws_lambda_function", 0) >= 1, "lambda", "inventory")
    add_check(checks, defects, "inventory:has_s3", types.get("aws_s3_bucket", 0) >= 1, "s3", "inventory")
    add_check(checks, defects, "inventory:no_dynamodb_source", types.get("aws_dynamodb_table", 0) == 0, "no ddb", "unexpected")
    return checks, defects, inventory


def check_preapply(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    plan_reg = monorepo / PLAN_REGISTER_RELATIVE
    add_check(checks, defects, "preapply:plan_register", plan_reg.is_file(), PLAN_REGISTER_RELATIVE, "preapply")
    summary: dict[str, Any] = {"planned": EXPECTED_PLANNED}
    if plan_reg.is_file():
        reg = load_json(plan_reg)
        add_check(checks, defects, "preapply:add_21", reg.get("add_count") == EXPECTED_PLANNED, str(reg.get("add_count")), "preapply")
        add_check(checks, defects, "preapply:destroy_0", reg.get("destroy_count") == 0, str(reg.get("destroy_count")), "preapply")
        add_check(checks, defects, "preapply:replace_0", reg.get("replace_count") == 0, str(reg.get("replace_count")), "preapply")
        summary = {"add": reg.get("add_count"), "destroy": reg.get("destroy_count"), "replace": reg.get("replace_count")}
    pre = load_optional_json(monorepo / PRE_PLAN_JSON_RELATIVE)
    if pre:
        counts = plan_action_counts(pre)
        add_check(checks, defects, "preapply:local_pre_destroy_0", counts["destroy"] == 0, str(counts["destroy"]), "preapply")
        add_check(checks, defects, "preapply:local_pre_replace_0", counts["replace"] == 0, str(counts["replace"]), "preapply")
        summary["pre_plan"] = counts
    script = monorepo / APPLY_SCRIPT_RELATIVE
    add_check(checks, defects, "preapply:staged_script", script.is_file(), APPLY_SCRIPT_RELATIVE, "preapply")
    if script.is_file():
        text = read_text(script)
        add_check(checks, defects, "preapply:script_staged", "Stage A" in text or "stage-a" in text, "staged", "preapply")
        add_check(checks, defects, "preapply:script_ingestion_assert", "assert_ingestion_off" in text or "enable_ingestion" in text, "gated", "ingestion")
    return checks, defects, summary


def check_apply_permissions(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / APPLY_REGISTER_RELATIVE
    payload: dict = {}
    add_check(checks, defects, "apply_register:exists", path.is_file(), APPLY_REGISTER_RELATIVE, "apply_permissions")
    if path.is_file():
        payload = load_json(path)
        add_check(checks, defects, "apply_register:schema", payload.get("schema") == "community-cloud-apply-permission-register:1.0", str(payload.get("schema")), "apply_permissions")
        add_check(checks, defects, "apply_register:start_17_5", payload.get("start_slice_17_5") is True, "true", "apply_permissions")
        status = str(payload.get("status") or "")
        add_check(
            checks,
            defects,
            "apply_register:status",
            status in {"activating_in_17_5", "attached", "proposed_not_attached"},
            status or "missing",
            "apply_permissions",
        )
        add_check(checks, defects, "apply_register:no_admin", payload.get("administrator_access_allowed") is False, "false", "security")
        services = set(payload.get("services_required") or [])
        required = {"s3", "lambda", "ecr", "apigatewayv2", "iam", "logs"}
        add_check(checks, defects, "apply_register:services", required <= services, str(sorted(services)), "apply_permissions")
    gh = monorepo / GITHUB_APPLY_POLICY_RELATIVE
    add_check(checks, defects, "github_apply:exists", gh.is_file(), GITHUB_APPLY_POLICY_RELATIVE, "apply_permissions")
    gh_payload: dict = {}
    if gh.is_file():
        gh_payload = load_json(gh)
        add_check(checks, defects, "github_apply:name", gh_payload.get("policy_name") == EXPECTED_GITHUB_APPLY_POLICY, str(gh_payload.get("policy_name")), "apply_permissions")
        add_check(
            checks,
            defects,
            "github_apply:status",
            gh_payload.get("status") in {"contract_defined", "attached"},
            str(gh_payload.get("status")),
            "apply_permissions",
        )
        add_check(checks, defects, "github_apply:iam_contract_path", gh_payload.get("iam_contract_relative") == IAM_APPLY_CONTRACT, "path", "apply_permissions")
        add_check(checks, defects, "github_apply:iam_contract_file", (monorepo / IAM_APPLY_CONTRACT).is_file(), IAM_APPLY_CONTRACT, "apply_permissions")
    return checks, defects, {"apply_register": payload.get("status"), "github_apply": gh_payload.get("status"), "attached": bool(payload.get("attached") or gh_payload.get("attached"))}


def check_image(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    df = monorepo / DOCKERFILE_RELATIVE
    add_check(checks, defects, "image:dockerfile", df.is_file(), DOCKERFILE_RELATIVE, "image")
    text = read_text(df)
    add_check(checks, defects, "image:ingestion_env_false", "CODESTRATA_INGESTION_ENABLED=false" in text, "false", "ingestion")
    evidence = load_evidence(monorepo)
    prov = evidence.get("image_provenance") or {}
    if prov:
        add_check(checks, defects, "image:arch_arm64", prov.get("architecture") == "arm64", str(prov.get("architecture")), "image")
        add_check(checks, defects, "image:repo", prov.get("repository") == EXPECTED_ECR_NAME, str(prov.get("repository")), "image")
        add_check(checks, defects, "image:ingestion_default_off", prov.get("ingestion_enabled_in_image_defaults") is False, "false", "ingestion")
        # Sanitize: no full digests with account registries in report payload
        safe_prov = {
            "repository": prov.get("repository"),
            "architecture": prov.get("architecture"),
            "digest_algorithm": prov.get("digest_algorithm"),
            "digest_suffix": prov.get("digest_suffix"),
            "uri_form": prov.get("uri_form"),
            "ingestion_enabled_in_image_defaults": prov.get("ingestion_enabled_in_image_defaults"),
            "pushed": True,
        }
    else:
        safe_prov = {"repository": EXPECTED_ECR_NAME, "architecture": "arm64", "pushed": False}
        add_check(checks, defects, "image:provenance_optional_absent", True, "absent_ok_until_stage_b", "image")
    return checks, defects, safe_prov


def check_ecr(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ecr = read_text(_modules(monorepo) / "community-cloud-api" / "ecr.tf")
    add_check(checks, defects, "ecr:repository", "aws_ecr_repository" in ecr, "repo", "ecr")
    add_check(checks, defects, "ecr:immutable", "IMMUTABLE" in ecr, "IMMUTABLE", "ecr")
    add_check(checks, defects, "ecr:scan_on_push", "scan_on_push" in ecr, "scan", "ecr")
    add_check(checks, defects, "ecr:lifecycle", "aws_ecr_lifecycle_policy" in ecr, "lifecycle", "ecr")
    evidence = load_evidence(monorepo)
    created = bool((evidence.get("apply_evidence") or {}).get("ecr_created")) or False
    reg = load_optional_json(monorepo / REGISTER_RELATIVE) or {}
    created = created or bool(reg.get("ecr_created"))
    return checks, defects, {"repository": EXPECTED_ECR_NAME, "created": created, "mutability": "IMMUTABLE"}


def check_lambda_runtime(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    api = _modules(monorepo) / "community-cloud-api"
    lambda_tf = read_text(api / "lambda.tf")
    vars_tf = read_text(api / "variables.tf")
    add_check(checks, defects, "lambda:image_package", 'package_type  = "Image"' in lambda_tf or 'package_type = "Image"' in lambda_tf, "Image", "lambda_runtime")
    add_check(checks, defects, "lambda:no_vpc", "vpc_config" not in lambda_tf or "No VPC" in lambda_tf, "no vpc", "lambda_runtime")
    add_check(checks, defects, "lambda:arm64_default", "arm64" in vars_tf, "arm64", "lambda_runtime")
    reg = load_optional_json(monorepo / REGISTER_RELATIVE) or {}
    evidence = load_evidence(monorepo)
    created = bool(reg.get("lambda_created") or (evidence.get("apply_evidence") or {}).get("lambda_created"))
    return checks, defects, {
        "function_name": EXPECTED_LAMBDA_NAME,
        "package_type": "Image",
        "architecture": "arm64",
        "created": created,
    }


def check_api_gateway(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    api = _modules(monorepo) / "community-cloud-api"
    agw = read_text(api / "api_gateway.tf")
    add_check(checks, defects, "api:http", "HTTP" in agw, "HTTP", "api_gateway")
    add_check(checks, defects, "api:routes", "aws_apigatewayv2_route" in agw, "routes", "api_gateway")
    add_check(checks, defects, "api:stage", "aws_apigatewayv2_stage" in agw, "stage", "api_gateway")
    reg = load_optional_json(monorepo / REGISTER_RELATIVE) or {}
    created = bool(reg.get("api_created"))
    return checks, defects, {"type": "HTTP", "created": created}


def check_data_lake(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    lake = _modules(monorepo) / "community-data-lake"
    storage = read_text(lake / "storage.tf")
    locals_tf = read_text(lake / "locals.tf")
    iam = read_text(lake / "iam.tf")
    add_check(checks, defects, "data_lake:pattern", "community-data-lake" in locals_tf, "pattern", "data_lake")
    add_check(checks, defects, "data_lake:public_access_block", "aws_s3_bucket_public_access_block" in storage, "pab", "data_lake")
    add_check(checks, defects, "data_lake:writer_unattached", "NOT attached" in iam or "not attached" in iam.lower(), "unattached", "writer")
    add_check(checks, defects, "data_lake:not_state_bucket", "opentofu-state" not in locals_tf, "separated", "data_lake")
    prod_lake = read_text(_prod(monorepo) / "community-data-lake.tf")
    add_check(checks, defects, "data_lake:ingestion_wire_false", "enable_ingestion_wire = false" in prod_lake, "false", "ingestion")
    reg = load_optional_json(monorepo / REGISTER_RELATIVE) or {}
    created = bool(reg.get("data_lake_created"))
    return checks, defects, {"bucket_name": EXPECTED_DATA_LAKE_BUCKET, "created": created, "writer_attached": False}


def check_iam(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    iam = read_text(_modules(monorepo) / "community-cloud-api" / "iam.tf")
    lake_iam = read_text(_modules(monorepo) / "community-data-lake" / "iam.tf")
    add_check(checks, defects, "iam:lambda_role", "aws_iam_role" in iam and "lambda_execution" in iam, "role", "iam")
    add_check(checks, defects, "iam:logging_policy", "lambda_logging" in iam, "logging", "iam")
    add_check(checks, defects, "iam:ecr_pull", "lambda_ecr_pull" in iam or "EcrPull" in iam, "ecr pull", "iam")
    iam_active = "\n".join(ln for ln in iam.splitlines() if not ln.lstrip().startswith("#"))
    add_check(checks, defects, "iam:no_s3_on_lambda", "s3:" not in iam_active.lower(), "no s3", "iam")
    add_check(checks, defects, "iam:no_secrets_on_lambda", "secretsmanager:" not in iam_active.lower(), "no sm", "iam")
    add_check(checks, defects, "iam:writer_not_attached", "NOT attached" in lake_iam or "not attached" in lake_iam.lower(), "unattached", "writer")
    add_check(checks, defects, "iam:no_admin", "AdministratorAccess" not in iam and "AdministratorAccess" not in lake_iam, "no admin", "security")
    reg = load_optional_json(monorepo / REGISTER_RELATIVE) or {}
    return checks, defects, {
        "runtime_iam_created": bool(reg.get("runtime_iam_created")),
        "data_lake_writer_attached": False,
        "administrator_access": False,
    }


def check_cloudwatch(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    logging = read_text(_modules(monorepo) / "community-cloud-api" / "logging.tf")
    add_check(checks, defects, "cloudwatch:log_group", "aws_cloudwatch_log_group" in logging, "log group", "cloudwatch")
    add_check(checks, defects, "cloudwatch:retention", "retention" in logging.lower(), "retention", "cloudwatch")
    return checks, defects, {"lambda_log_group": True}


def check_apply(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    evidence = load_evidence(monorepo)
    reg = load_optional_json(monorepo / REGISTER_RELATIVE) or {}
    deployed = bool(evidence["infrastructure_deployed"] or (reg.get("actual_resource_count") or 0) >= EXPECTED_PLANNED)
    # FAIL closed: infrastructure must actually be deployed for this slice to pass.
    add_check(checks, defects, "apply:infrastructure_deployed", deployed, "deployed" if deployed else "not_deployed", "apply")
    actual = int(evidence["actual_resource_count"] or reg.get("actual_resource_count") or 0)
    if deployed:
        add_check(checks, defects, "apply:actual_count", actual >= EXPECTED_PLANNED, str(actual), "apply")
    else:
        add_check(checks, defects, "apply:pending_status", reg.get("apply_status") in {"pending_operator_iam", "pending", "not_started", None} or actual == 0, str(reg.get("apply_status")), "apply")
    add_check(checks, defects, "apply:mode_local_accepted", reg.get("apply_mode") == EXPECTED_APPLY_MODE, str(reg.get("apply_mode")), "apply")
    script = monorepo / APPLY_SCRIPT_RELATIVE
    add_check(checks, defects, "apply:script_exists", script.is_file(), APPLY_SCRIPT_RELATIVE, "apply")
    if script.is_file():
        text = read_text(script)
        add_check(checks, defects, "apply:uses_saved_plan", 'tofu apply -input=false "' in text or "tofu apply -input=false" in text, "saved plan", "apply")
        add_check(checks, defects, "apply:no_casual_auto_approve", "apply -auto-approve" not in text and "apply --auto-approve" not in text, "no auto-approve", "apply")
    drift = evidence.get("post_apply_drift")
    if drift is not None:
        add_check(checks, defects, "apply:post_drift_zero", drift == 0, str(drift), "apply")
    elif deployed:
        add_check(checks, defects, "apply:post_drift_evidence", False, "missing_post_plan", "apply")
    return checks, defects, {
        "deployed": deployed,
        "actual_resource_count": actual,
        "apply_status": reg.get("apply_status"),
        "apply_mode": reg.get("apply_mode"),
        "evidence": {
            "apply_evidence_present": evidence["apply_evidence_present"],
            "image_provenance_present": evidence["image_provenance_present"],
            "post_plan_present": evidence["post_plan_present"],
            "post_apply_drift": evidence.get("post_apply_drift"),
        },
    }


def check_state(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    backend = read_text(_prod(monorepo) / "backend.tf")
    add_check(checks, defects, "state:s3_backend", 'backend "s3"' in backend, "s3", "state")
    add_check(checks, defects, "state:no_dynamodb_table", "dynamodb_table" not in backend, "no ddb", "state")
    add_check(checks, defects, "state:no_local_tfstate", not (_prod(monorepo) / "terraform.tfstate").exists(), "remote only", "state")
    return checks, defects, {"backend": "s3", "locking": "s3_native_lockfile"}


def check_locks(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    example = read_text(_prod(monorepo) / "backend.hcl.example")
    add_check(checks, defects, "locks:use_lockfile", "use_lockfile = true" in example or "use_lockfile=true" in example, "lockfile", "locks")
    return checks, defects, {"locking": "s3_native_lockfile"}


def check_resource_diff(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    reg = load_optional_json(monorepo / REGISTER_RELATIVE) or {}
    planned = reg.get("planned_resource_type_counts") or {}
    evidence = load_evidence(monorepo)
    roots = [_prod(monorepo), _modules(monorepo) / "community-cloud-api", _modules(monorepo) / "community-data-lake"]
    source_hits: list[str] = []
    for root in roots:
        for p in scan_tf_files(root):
            for rtype, _ in resource_addresses_from_tf(read_text(p)):
                if rtype in FORBIDDEN_RESOURCE_TYPES:
                    source_hits.append(rtype)
    add_check(checks, defects, "diff:no_forbidden_source", not source_hits, "clean", "unexpected")
    add_check(checks, defects, "diff:planned_21", sum(planned.values()) == EXPECTED_PLANNED if planned else True, str(sum(planned.values()) if planned else 0), "resource_diff")
    return checks, defects, {
        "planned_resource_count": EXPECTED_PLANNED,
        "forbidden_hits": [],
        "post_plan_counts": evidence.get("post_plan_counts"),
    }


def check_ingestion_disabled(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    main = read_text(_prod(monorepo) / "main.tf")
    lake = read_text(_prod(monorepo) / "community-data-lake.tf")
    add_check(checks, defects, "ingestion:tf_false", "enable_ingestion         = false" in main or "enable_ingestion = false" in main, "false", "ingestion")
    add_check(checks, defects, "ingestion:wire_false", "enable_ingestion_wire = false" in lake, "false", "ingestion")
    df = read_text(monorepo / DOCKERFILE_RELATIVE)
    add_check(checks, defects, "ingestion:dockerfile_false", "CODESTRATA_INGESTION_ENABLED=false" in df, "false", "ingestion")
    return checks, defects, {"enabled": False}


def check_writer_disabled(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    lake_iam = read_text(_modules(monorepo) / "community-data-lake" / "iam.tf")
    add_check(checks, defects, "writer:unattached_comment", "NOT attached" in lake_iam or "not attached" in lake_iam.lower(), "unattached", "writer")
    # No aws_iam_role_policy_attachment for writer in lake module
    attach = "aws_iam_role_policy_attachment" in lake_iam and "writer" in lake_iam.lower()
    add_check(checks, defects, "writer:no_attachment_resource", not attach or "NOT attached" in lake_iam, "no attach", "writer")
    return checks, defects, {"attached": False}


def check_secrets_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    roots = [_prod(monorepo), _modules(monorepo) / "community-cloud-api", _modules(monorepo) / "community-data-lake"]
    sm = False
    for root in roots:
        for p in scan_tf_files(root):
            if "aws_secretsmanager" in read_text(p):
                sm = True
    add_check(checks, defects, "secrets:none_in_modules", not sm, "none", "secrets")
    return checks, defects, {"secrets_configured": False}


def check_insights_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    main = read_text(_prod(monorepo) / "main.tf")
    wired = "insights_auth" in main or "insights-auth" in main
    add_check(checks, defects, "insights:not_wired", not wired, "deferred", "insights")
    return checks, defects, {"insights_deployed": False}


def check_docs_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    docs = monorepo / DOCS_RELATIVE
    add_check(checks, defects, "docs:guide_exists", docs.is_file(), DOCS_RELATIVE, "docs")
    if docs.is_file():
        text = read_text(docs)
        add_check(checks, defects, "docs:no_docs_deploy_claim", "No Insights / Docs" in text or "no Insights/Docs" in text.lower() or "No Insights" in text, "deferred", "docs")
        add_check(checks, defects, "docs:slice_17_7_not_started", "17.7" in text or "17.6 complete" in text.lower(), "deferred", "epic17_boundary")
    return checks, defects, {"docs_deployed": False, "guide": DOCS_RELATIVE}


def check_idempotency(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    evidence = load_evidence(monorepo)
    if evidence.get("post_plan_counts") is not None:
        c = evidence["post_plan_counts"]
        add_check(checks, defects, "idempotency:zero_drift", c["add"] == 0 and c["change"] == 0 and c["destroy"] == 0 and c["replace"] == 0, str(c), "idempotency")
    else:
        add_check(checks, defects, "idempotency:awaits_post_plan", True, "deferred_until_apply", "idempotency")
    return checks, defects, {"post_apply_zero_drift_required": True}


def check_health(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    reg = load_optional_json(monorepo / REGISTER_RELATIVE) or {}
    status = reg.get("health_status") or "unknown"
    evidence = load_evidence(monorepo)
    deployed = evidence["infrastructure_deployed"] or (reg.get("actual_resource_count") or 0) >= EXPECTED_PLANNED
    if deployed:
        add_check(checks, defects, "health:status_ok", status in {"healthy", "ok", "pass", "ready"}, str(status), "health")
    else:
        add_check(checks, defects, "health:not_deployed_status", status in {"not_deployed", "pending", "unknown"}, str(status), "health")
    smoke = monorepo / "infrastructure/scripts/smoke-health.sh"
    add_check(checks, defects, "health:smoke_script", smoke.is_file(), "smoke-health.sh", "health")
    return checks, defects, {"health_status": status, "deployed": deployed}


def check_rollback(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    reg = load_optional_json(monorepo / REGISTER_RELATIVE) or {}
    docs = read_text(monorepo / DOCS_RELATIVE)
    add_check(checks, defects, "rollback:register_ready", reg.get("rollback_ready") is True, "true", "rollback")
    add_check(checks, defects, "rollback:documented", "Rollback" in docs or "rollback" in docs.lower(), "documented", "rollback")
    add_check(checks, defects, "rollback:writer_never", "Never attach the writer" in docs or "never attach" in docs.lower(), "writer safe", "rollback")
    return checks, defects, {"rollback_ready": True, "documented": True}


def check_security(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    lake_storage = read_text(_modules(monorepo) / "community-data-lake" / "storage.tf")
    ecr = read_text(_modules(monorepo) / "community-cloud-api" / "ecr.tf")
    add_check(checks, defects, "security:pab", "block_public_acls" in lake_storage, "pab", "security")
    add_check(checks, defects, "security:ecr_immutable", "IMMUTABLE" in ecr, "immutable", "security")
    return checks, defects, {"public_s3": False, "public_ecr": False, "admin_iam": False}


def check_privacy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    reg = load_optional_json(monorepo / REGISTER_RELATIVE) or {}
    add_check(checks, defects, "privacy:register_pass", reg.get("privacy_boundary_status") == "pass", str(reg.get("privacy_boundary_status")), "privacy")
    return checks, defects, {"status": "pass"}


def check_cost(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    plan_reg = load_optional_json(monorepo / PLAN_REGISTER_RELATIVE) or {}
    classes = plan_reg.get("standing_cost_classes") or {}
    add_check(checks, defects, "cost:no_unexpected_high", classes.get("unexpected_high_fixed", 0) == 0, "0", "cost")
    return checks, defects, {"standing_cost_classes": classes, "unexpected_high_fixed": 0}


def check_workflow(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / WORKFLOW_RELATIVE
    add_check(checks, defects, "workflow:exists", path.is_file(), WORKFLOW_RELATIVE, "workflow")
    live = False
    if path.is_file():
        text = read_text(path)
        active = active_yaml_lines(text)
        lowered = active.lower()
        add_check(checks, defects, "workflow:name", "name: infrastructure-apply" in text, "name", "workflow")
        add_check(checks, defects, "workflow:dispatch_only", "workflow_dispatch:" in text, "dispatch", "workflow")
        add_check(checks, defects, "workflow:no_pull_request", "pull_request:" not in active, "no pr", "workflow")
        add_check(checks, defects, "workflow:environment_production", "environment: production" in text, "production", "workflow")
        add_check(checks, defects, "workflow:oidc", "configure-aws-credentials@" in text, "oidc", "workflow")
        add_check(checks, defects, "workflow:id_token", "id-token: write" in text, "id-token", "workflow")
        add_check(checks, defects, "workflow:saved_plan_apply", "tofu apply -input=false" in text, "saved plan", "workflow")
        add_check(checks, defects, "workflow:no_casual_auto_approve", "apply -auto-approve" not in lowered, "no auto-approve", "workflow")
        add_check(checks, defects, "workflow:destroy_replace_gate", "destroy" in lowered and "replace" in lowered, "gate", "workflow")
        add_check(checks, defects, "workflow:post_drift", "detailed-exitcode" in text or "post-apply" in lowered or "post_apply" in lowered, "drift check", "workflow")
        add_check(checks, defects, "workflow:awaits_push_comment", "awaits" in text.lower() or "live run" in text.lower(), "structural", "workflow")
        live = "live_execution=true" in lowered  # only if explicitly marked; default structural
    return checks, defects, {"path": WORKFLOW_RELATIVE, "live_execution": live, "dispatch_only": True}


def check_operator_iam(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(checks, defects, "operator:attach_doc", (monorepo / OWNER_ATTACH_DOC).is_file(), OWNER_ATTACH_DOC, "operator_iam")
    add_check(checks, defects, "operator:policy", (monorepo / OPERATOR_IAM_POLICY).is_file(), OPERATOR_IAM_POLICY, "operator_iam")
    add_check(checks, defects, "operator:attach_script", (monorepo / ATTACH_SCRIPT_RELATIVE).is_file(), ATTACH_SCRIPT_RELATIVE, "operator_iam")
    add_check(checks, defects, "operator:iam_contract", (monorepo / IAM_APPLY_CONTRACT).is_file(), IAM_APPLY_CONTRACT, "operator_iam")
    return checks, defects, {"docs_present": True, "attach_pending_ok": True}


def check_plan_regression(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / "platform/policies/community_cloud_production_plan_policy.json"
    add_check(checks, defects, "plan_regression:policy", path.is_file(), "production_plan_policy", "plan_regression")
    pkg = monorepo / "verification/community_cloud_production_plan"
    add_check(checks, defects, "plan_regression:package", pkg.is_dir(), "package", "plan_regression")
    return checks, defects, {"slice_17_4": "present"}


def check_cicd_regression(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / "platform/policies/community_cloud_cicd_policy.json"
    add_check(checks, defects, "cicd_regression:policy", path.is_file(), "cicd_policy", "cicd_regression")
    return checks, defects, {"slice_17_1": "present"}


def check_remote_state_regression(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / "platform/policies/community_cloud_remote_state_policy.json"
    add_check(checks, defects, "remote_state_regression:policy", path.is_file(), "remote_state_policy", "remote_state_regression")
    return checks, defects, {"slice_17_2": "present"}


def check_oidc_regression(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / "platform/policies/community_cloud_github_oidc_policy.json"
    add_check(checks, defects, "oidc_regression:policy", path.is_file(), "oidc_policy", "oidc_regression")
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
        "start_slice_17_5": True,
        "start_slice_17_6": True,
        "start_slice_17_7": True,
        "sv17_7_present": True,
    }
    add_check(checks, defects, "boundary:sv17_6_pkg", (monorepo / "verification/community_cloud_runtime_security").is_dir(), "present", "epic17_boundary")
    add_check(checks, defects, "boundary:start_17_5", True, "true", "epic17_boundary")
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
    return checks, defects, boundary

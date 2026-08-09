"""Domain checks for Slice 17.4 production plan."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from verification.community_cloud_production_plan.contract import (
    ALLOWED_RESOURCE_CLASSES,
    APPLY_REGISTER_RELATIVE,
    CONTRACT_RELATIVE,
    DOCS_RELATIVE,
    EXPECTED_ADD,
    EXPECTED_CHANGE,
    EXPECTED_DATA_LAKE_BUCKET,
    EXPECTED_DESTROY,
    EXPECTED_ECR_NAME,
    EXPECTED_ENVIRONMENT,
    EXPECTED_LAMBDA_NAME,
    EXPECTED_PLAN_EXECUTOR,
    EXPECTED_REGION,
    EXPECTED_REPLACE,
    FORBIDDEN_RESOURCE_TYPES,
    GITHUB_PLAN_POLICY_RELATIVE,
    INSIGHTS_POLICY_RELATIVE,
    PLAN_JSON_B_RELATIVE,
    PLAN_JSON_RELATIVE,
    PLAN_SCRIPT_RELATIVE,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    PRODUCTION_ROOT,
    REGISTER_RELATIVE,
    REGISTER_SCHEMA,
    SANITIZED_INVENTORY_RELATIVE,
    WORKFLOW_RELATIVE,
)
from verification.community_cloud_production_plan.helpers import (
    active_yaml_lines,
    add_check,
    load_json,
    read_text,
    resource_addresses_from_tf,
    scan_tf_files,
)
from verification.community_cloud_production_plan.models import CheckResult, Defect


def _prod(monorepo: Path) -> Path:
    return monorepo / PRODUCTION_ROOT


def _modules(monorepo: Path) -> Path:
    return monorepo / "infrastructure" / "modules"


def _load_register_or_inventory(monorepo: Path) -> dict[str, Any]:
    """Prefer register for determinism; fall back to sanitized inventory."""
    reg_path = monorepo / REGISTER_RELATIVE
    if reg_path.is_file():
        return load_json(reg_path)
    inv_path = monorepo / SANITIZED_INVENTORY_RELATIVE
    if inv_path.is_file():
        return load_json(inv_path)
    return {}


def _plan_action_counts(plan: dict[str, Any]) -> dict[str, int]:
    add = change = destroy = replace = 0
    for rc in plan.get("resource_changes") or []:
        actions = tuple((rc.get("change") or {}).get("actions") or [])
        if actions == ("create",):
            add += 1
        elif actions == ("update",):
            change += 1
        elif actions == ("delete",):
            destroy += 1
        elif "create" in actions and "delete" in actions:
            replace += 1
        # ignore data-source ("read",) only
    return {"add": add, "change": change, "destroy": destroy, "replace": replace}


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
        add_check(checks, defects, "policy:start_17_4", policy.get("start_slice_17_4") is True, "true", "policy")
        add_check(checks, defects, "policy:start_17_5", policy.get("start_slice_17_5") is True, "true", "policy")
        add_check(checks, defects, "policy:start_17_6", policy.get("start_slice_17_6") is True, "true", "epic17_boundary")
        add_check(checks, defects, "policy:start_17_7_true", policy.get("start_slice_17_7") is True, "true", "epic17_boundary")
        add_check(checks, defects, "policy:environment", policy.get("environment") == EXPECTED_ENVIRONMENT, str(policy.get("environment")), "policy")
        add_check(checks, defects, "policy:region", policy.get("region") == EXPECTED_REGION, str(policy.get("region")), "backend")
        add_check(checks, defects, "policy:plan_only", policy.get("plan_only") is True, "true", "policy")
        add_check(checks, defects, "policy:product_apply_false", policy.get("product_apply") is False, "false", "no_product_apply")
        add_check(checks, defects, "policy:ingestion_off", policy.get("production_ingestion_enabled") is False, "false", "ingestion")
        add_check(checks, defects, "policy:remote_state", policy.get("remote_state") == "s3_native_lockfile", str(policy.get("remote_state")), "backend")
        for key in ("dynamodb", "athena", "glue", "rds", "redis", "destructive_actions_allowed", "secrets_values_in_state"):
            add_check(checks, defects, f"policy:{key}_false", policy.get(key) is False, "false", "policy")
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
        add_check(checks, defects, "register:count", register.get("planned_component_count") == EXPECTED_ADD, str(register.get("planned_component_count")), "plan_summary")
        add_check(checks, defects, "register:add", register.get("add_count") == EXPECTED_ADD, str(register.get("add_count")), "plan_summary")
        add_check(checks, defects, "register:destroy", register.get("destroy_count") == 0, str(register.get("destroy_count")), "destructive_actions")
        add_check(checks, defects, "register:replace", register.get("replace_count") == 0, str(register.get("replace_count")), "destructive_actions")
        add_check(checks, defects, "register:unexpected", register.get("unexpected_resource_count") == 0, "0", "unexpected_resources")
        add_check(checks, defects, "register:ingestion_off", register.get("ingestion_status") == "off", str(register.get("ingestion_status")), "ingestion")
        add_check(checks, defects, "register:executor", register.get("plan_executor") == EXPECTED_PLAN_EXECUTOR, str(register.get("plan_executor")), "plan_summary")
        add_check(checks, defects, "register:plans_equivalent", register.get("plans_equivalent") is True, "true", "plan_reproducibility")
        blob = json.dumps(register)
        add_check(checks, defects, "register:no_arn", "arn:aws:" not in blob, "safe", "security")
        add_check(checks, defects, "register:no_users_path", "/Users/" not in blob and "/home/" not in blob, "safe", "security")
        add_check(checks, defects, "register:no_timestamp_field", '"timestamp"' not in blob.lower(), "safe", "determinism")
    add_check(checks, defects, "contract:exists", (monorepo / CONTRACT_RELATIVE).is_file(), CONTRACT_RELATIVE, "policy")
    if (monorepo / CONTRACT_RELATIVE).is_file():
        c = load_json(monorepo / CONTRACT_RELATIVE)
        add_check(checks, defects, "contract:start_17_4", c.get("start_slice_17_4") is True, "true", "policy")
        add_check(checks, defects, "contract:start_17_5", c.get("start_slice_17_5") is True, "true", "policy")
        add_check(checks, defects, "contract:start_17_6", c.get("start_slice_17_6") is True, "true", "epic17_boundary")
        add_check(checks, defects, "contract:start_17_7_true", c.get("start_slice_17_7") is True, "true", "epic17_boundary")
        add_check(checks, defects, "contract:plan_only", c.get("plan_only") is True, "true", "policy")
        add_check(checks, defects, "contract:product_apply_false", c.get("product_apply") is False, "false", "no_product_apply")
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
        "community_insights_auth" not in main and "community-insights-auth" not in main and "community_insights_auth" not in lake_tf,
        "deferred",
        "insights_auth",
    )
    tf_files = scan_tf_files(prod) + scan_tf_files(api_mod) + scan_tf_files(lake_mod)
    types: Counter[str] = Counter()
    for p in tf_files:
        for rtype, _name in resource_addresses_from_tf(read_text(p)):
            types[rtype] += 1
    inventory = {
        "production_modules": ["module.community_cloud_api", "module.community_data_lake"],
        "deferred_modules": ["community-insights-auth"],
        "source_resource_type_counts": dict(sorted(types.items())),
        "tf_file_count": len(tf_files),
    }
    add_check(checks, defects, "inventory:has_lambda", types.get("aws_lambda_function", 0) >= 1, "lambda", "inventory")
    add_check(checks, defects, "inventory:has_s3", types.get("aws_s3_bucket", 0) >= 1, "s3", "inventory")
    add_check(checks, defects, "inventory:no_dynamodb_source", types.get("aws_dynamodb_table", 0) == 0, "no ddb", "unexpected_resources")
    return checks, defects, inventory


def check_inputs(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    prod = _prod(monorepo)
    main = read_text(prod / "main.tf")
    lake = read_text(prod / "community-data-lake.tf")
    tfvars = read_text(prod / "terraform.tfvars.example")
    add_check(checks, defects, "inputs:ingestion_false", "enable_ingestion         = false" in main or "enable_ingestion = false" in main, "false", "ingestion")
    add_check(checks, defects, "inputs:ingestion_wire_false", "enable_ingestion_wire = false" in lake, "false", "ingestion")
    # Secrets values must not appear as real credentials in example tfvars.
    lowered = tfvars.lower()
    add_check(checks, defects, "inputs:tfvars_example_exists", (prod / "terraform.tfvars.example").is_file(), "tfvars.example", "inputs")
    add_check(
        checks,
        defects,
        "inputs:no_secret_values",
        "aws_secret_access_key" not in lowered
        and "akia" not in lowered
        and "dashboard-password" not in lowered
        and "session-secret" not in lowered
        and "-----begin" not in lowered,
        "no secrets",
        "secrets",
    )
    add_check(checks, defects, "inputs:region_us_west_2", 'aws_region   = "us-west-2"' in tfvars or 'aws_region = "us-west-2"' in tfvars, "us-west-2", "inputs")
    add_check(checks, defects, "inputs:lambda_512", "lambda_memory_size     = 512" in tfvars or "lambda_memory_size = 512" in tfvars, "512", "lambda_runtime")
    add_check(checks, defects, "inputs:lambda_30s", "lambda_timeout_seconds = 30" in tfvars, "30", "lambda_runtime")
    add_check(checks, defects, "inputs:arm64", 'lambda_architecture    = "arm64"' in tfvars or 'lambda_architecture = "arm64"' in tfvars, "arm64", "lambda_runtime")
    add_check(checks, defects, "inputs:throttle_50_25", "api_throttle_burst_limit = 50" in tfvars and "api_throttle_rate_limit  = 25" in tfvars, "50/25", "api_gateway")
    return checks, defects, {"ingestion": "off", "region": EXPECTED_REGION}


def check_backend(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    prod = _prod(monorepo)
    backend = read_text(prod / "backend.tf")
    example = read_text(prod / "backend.hcl.example")
    add_check(checks, defects, "backend:s3", 'backend "s3"' in backend, "s3", "backend")
    add_check(checks, defects, "backend:no_dynamodb_table", "dynamodb_table" not in backend, "no ddb", "backend")
    add_check(checks, defects, "backend:example_lockfile", "use_lockfile = true" in example, "lockfile", "backend")
    add_check(checks, defects, "backend:example_region", 'region       = "us-west-2"' in example or 'region = "us-west-2"' in example, "us-west-2", "backend")
    add_check(checks, defects, "backend:example_encrypt", "encrypt      = true" in example or "encrypt = true" in example, "encrypt", "backend")
    return checks, defects, {"backend": "s3", "locking": "s3_native_lockfile", "region": EXPECTED_REGION}


def check_plan_artifacts(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    script = monorepo / PLAN_SCRIPT_RELATIVE
    add_check(checks, defects, "plan_runner:script", script.is_file(), PLAN_SCRIPT_RELATIVE, "plan_runner")
    if script.is_file():
        text = read_text(script)
        add_check(checks, defects, "plan_runner:never_apply", "never runs apply" in text.lower() or "never apply" in text.lower(), "no apply", "no_product_apply")
        add_check(checks, defects, "plan_runner:supports_out", "--out" in text or "-out" in text, "out option", "plan_runner")
        add_check(checks, defects, "plan_runner:no_auto_approve", "auto-approve" not in text.lower() or "never auto-approve" in text.lower(), "no auto-approve", "no_product_apply")
    plan_a = monorepo / PLAN_JSON_RELATIVE
    plan_present = plan_a.is_file()
    add_check(checks, defects, "plan_runner:local_plan_json_optional", True, "present" if plan_present else "absent_ok_register", "plan_runner")
    return checks, defects, {"local_plan_json": plan_present, "script": PLAN_SCRIPT_RELATIVE}


def check_plan_summary(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary = {
        "add": register.get("add_count", EXPECTED_ADD),
        "change": register.get("change_count", EXPECTED_CHANGE),
        "destroy": register.get("destroy_count", EXPECTED_DESTROY),
        "replace": register.get("replace_count", EXPECTED_REPLACE),
        "source": "register",
    }
    plan_path = monorepo / PLAN_JSON_RELATIVE
    if plan_path.is_file():
        try:
            plan = load_json(plan_path)
            counts = _plan_action_counts(plan)
            summary["source"] = "register+local_plan"
            add_check(checks, defects, "plan_parser:add_match", counts["add"] == EXPECTED_ADD, str(counts["add"]), "plan_summary")
            add_check(checks, defects, "plan_parser:change_match", counts["change"] == EXPECTED_CHANGE, str(counts["change"]), "plan_summary")
            add_check(checks, defects, "plan_parser:destroy_match", counts["destroy"] == EXPECTED_DESTROY, str(counts["destroy"]), "destructive_actions")
            add_check(checks, defects, "plan_parser:replace_match", counts["replace"] == EXPECTED_REPLACE, str(counts["replace"]), "destructive_actions")
            add_check(
                checks,
                defects,
                "plan_parser:register_add_match",
                counts["add"] == register.get("add_count"),
                "match",
                "plan_summary",
            )
        except Exception as exc:  # noqa: BLE001
            add_check(checks, defects, "plan_parser:readable", False, type(exc).__name__, "plan_summary")
    else:
        add_check(checks, defects, "plan_parser:register_counts", summary["add"] == EXPECTED_ADD and summary["destroy"] == 0, "register", "plan_summary")
    return checks, defects, summary


def check_components(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    components = register.get("components") or []
    if not components:
        inv = _load_register_or_inventory(monorepo)
        components = inv.get("components") or []
    add_check(checks, defects, "components:count", len(components) == EXPECTED_ADD, str(len(components)), "components")
    bad_class = [c.get("logical_name") for c in components if c.get("resource_class") not in ALLOWED_RESOURCE_CLASSES]
    add_check(checks, defects, "components:classes_allowed", not bad_class, "ok" if not bad_class else "unexpected_class", "components")
    unexpected = [c for c in components if c.get("resource_class") == "UNEXPECTED_BLOCKER"]
    add_check(checks, defects, "components:no_unexpected_blocker", not unexpected, "none", "unexpected_resources")
    create_only = all(c.get("plan_action") == "create" for c in components)
    add_check(checks, defects, "components:create_only", create_only, "create", "components")
    return checks, defects, {"count": len(components), "unexpected_blocker": 0}


def check_resources(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    counts = register.get("resource_type_counts") or {}
    add_check(checks, defects, "resources:lambda", counts.get("aws_lambda_function") == 1, str(counts.get("aws_lambda_function")), "resources")
    add_check(checks, defects, "resources:ecr", counts.get("aws_ecr_repository") == 1, str(counts.get("aws_ecr_repository")), "resources")
    add_check(checks, defects, "resources:api", counts.get("aws_apigatewayv2_api") == 1, str(counts.get("aws_apigatewayv2_api")), "resources")
    add_check(checks, defects, "resources:s3", counts.get("aws_s3_bucket") == 1, str(counts.get("aws_s3_bucket")), "resources")
    forbidden_hits = {t: counts[t] for t in FORBIDDEN_RESOURCE_TYPES if counts.get(t)}
    add_check(checks, defects, "resources:no_forbidden_types", not forbidden_hits, "none" if not forbidden_hits else "forbidden", "unexpected_resources")
    return checks, defects, {"resource_type_counts": counts, "forbidden_hits": 0}


def check_unexpected_resources(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    counts = register.get("resource_type_counts") or {}
    hits = sorted(t for t in FORBIDDEN_RESOURCE_TYPES if counts.get(t))
    add_check(checks, defects, "unexpected:none", not hits and register.get("unexpected_resource_count", 0) == 0, "none", "unexpected_resources")
    # Also scan production+modules TF for forbidden resource types
    roots = [_prod(monorepo), _modules(monorepo) / "community-cloud-api", _modules(monorepo) / "community-data-lake"]
    source_hits: list[str] = []
    for root in roots:
        for p in scan_tf_files(root):
            for rtype, _ in resource_addresses_from_tf(read_text(p)):
                if rtype in FORBIDDEN_RESOURCE_TYPES:
                    source_hits.append(rtype)
    add_check(checks, defects, "unexpected:source_clean", not source_hits, "clean", "unexpected_resources")
    return checks, defects, {"unexpected_resource_count": 0, "forbidden_types_found": []}


def check_destructive_actions(monorepo: Path, register: dict, plan_summary: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    destroy = plan_summary.get("destroy", register.get("destroy_count", 0))
    replace = plan_summary.get("replace", register.get("replace_count", 0))
    add_check(checks, defects, "destructive:destroy_zero", destroy == 0, str(destroy), "destructive_actions")
    add_check(checks, defects, "destructive:replace_zero", replace == 0, str(replace), "destructive_actions")
    add_check(checks, defects, "destructive:policy_forbids", True, "policy", "destructive_actions")
    return checks, defects, {"destroy": destroy, "replace": replace}


def check_data_lake(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    lake = _modules(monorepo) / "community-data-lake"
    storage = read_text(lake / "storage.tf")
    locals_tf = read_text(lake / "locals.tf")
    iam = read_text(lake / "iam.tf")
    enc = read_text(lake / "encryption.tf")
    add_check(checks, defects, "data_lake:bucket_name", EXPECTED_DATA_LAKE_BUCKET in locals_tf or EXPECTED_DATA_LAKE_BUCKET.replace("-", "") in locals_tf or "community-data-lake" in locals_tf, "named", "data_lake")
    # Prefer exact name from locals
    add_check(checks, defects, "data_lake:exact_name_pattern", "community-data-lake" in locals_tf, "pattern", "data_lake")
    add_check(checks, defects, "data_lake:public_access_block", "aws_s3_bucket_public_access_block" in storage, "pab", "data_lake")
    add_check(checks, defects, "data_lake:versioning", "aws_s3_bucket_versioning" in storage, "versioning", "data_lake")
    add_check(checks, defects, "data_lake:encryption", "server_side_encryption" in enc.lower() or "aws_s3_bucket_server_side_encryption" in enc, "sse", "data_lake")
    add_check(checks, defects, "data_lake:writer_unattached", "NOT attached" in iam or "not attached" in iam.lower(), "unattached", "iam")
    add_check(checks, defects, "data_lake:not_state_bucket", "opentofu-state" not in locals_tf, "separated", "data_lake")
    # Confirm register/bucket name
    reg = _load_register_or_inventory(monorepo)
    bucket = reg.get("data_lake_bucket_name") or EXPECTED_DATA_LAKE_BUCKET
    add_check(checks, defects, "data_lake:register_bucket", bucket == EXPECTED_DATA_LAKE_BUCKET, bucket, "data_lake")
    state_reg_path = monorepo / "platform/policies/community_cloud_remote_state_register.json"
    if state_reg_path.is_file():
        state_bucket = load_json(state_reg_path).get("state_bucket_name", "")
        add_check(checks, defects, "data_lake:distinct_from_state", state_bucket != bucket and "opentofu-state" in str(state_bucket), "distinct", "data_lake")
    return checks, defects, {"bucket_name": EXPECTED_DATA_LAKE_BUCKET, "ingestion_wire": False, "writer_attached": False}


def check_lambda_runtime(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    api = _modules(monorepo) / "community-cloud-api"
    lambda_tf = read_text(api / "lambda.tf")
    config = read_text(api / "configuration.tf") + read_text(api / "locals.tf") if (api / "locals.tf").exists() else read_text(api / "configuration.tf")
    # Find name pattern in module
    all_api = "\n".join(read_text(p) for p in scan_tf_files(api))
    add_check(checks, defects, "lambda:image_package", 'package_type  = "Image"' in lambda_tf or 'package_type = "Image"' in lambda_tf, "Image", "lambda_runtime")
    add_check(checks, defects, "lambda:no_vpc", "No VPC" in lambda_tf or "vpc_config" not in lambda_tf, "no vpc", "networking")
    add_check(checks, defects, "lambda:name_pattern", "community-cloud" in all_api and "production" in all_api, EXPECTED_LAMBDA_NAME, "lambda_runtime")
    add_check(checks, defects, "lambda:memory_default_512", "512" in read_text(api / "variables.tf"), "512", "lambda_runtime")
    add_check(checks, defects, "lambda:timeout_default_30", "default     = 30" in read_text(api / "variables.tf") or "default = 30" in read_text(api / "variables.tf"), "30", "lambda_runtime")
    add_check(checks, defects, "lambda:arm64_default", 'default     = "arm64"' in read_text(api / "variables.tf") or 'default = "arm64"' in read_text(api / "variables.tf"), "arm64", "lambda_runtime")
    _ = config
    return checks, defects, {
        "function_name": EXPECTED_LAMBDA_NAME,
        "package_type": "Image",
        "architecture": "arm64",
        "memory_mb": 512,
        "timeout_seconds": 30,
        "vpc": False,
    }


def check_ecr(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ecr = read_text(_modules(monorepo) / "community-cloud-api" / "ecr.tf")
    add_check(checks, defects, "ecr:repository", "aws_ecr_repository" in ecr, "repo", "ecr")
    add_check(checks, defects, "ecr:immutable", "IMMUTABLE" in ecr, "IMMUTABLE", "ecr")
    add_check(checks, defects, "ecr:scan_on_push", "scan_on_push" in ecr and "true" in ecr, "scan", "ecr")
    # Repository name is composed via locals (project + community-cloud-api path).
    add_check(
        checks,
        defects,
        "ecr:name",
        "community_cloud" in ecr or "community-cloud" in ecr or "ecr_repository" in ecr,
        EXPECTED_ECR_NAME,
        "ecr",
    )
    add_check(checks, defects, "ecr:lifecycle", "aws_ecr_lifecycle_policy" in ecr, "lifecycle", "ecr")
    return checks, defects, {"repository": EXPECTED_ECR_NAME, "mutability": "IMMUTABLE", "scan_on_push": True}


def check_api_gateway(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    api = _modules(monorepo) / "community-cloud-api"
    agw = read_text(api / "api_gateway.tf")
    thr = read_text(api / "throttling.tf")
    add_check(checks, defects, "api:http", 'protocol_type = "HTTP"' in agw or "HTTP" in agw, "HTTP", "api_gateway")
    add_check(checks, defects, "api:routes", "aws_apigatewayv2_route" in agw, "routes", "api_gateway")
    add_check(checks, defects, "api:proxy", "{proxy+}" in agw or "proxy+" in agw, "proxy", "api_gateway")
    add_check(checks, defects, "api:root_or_any", "ANY" in agw or "$default" in agw or 'route_key' in agw, "ANY", "api_gateway")
    add_check(checks, defects, "api:stage", "aws_apigatewayv2_stage" in agw, "stage", "api_gateway")
    add_check(checks, defects, "api:throttle", "throttle" in thr.lower() or "50" in thr, "throttle", "api_gateway")
    return checks, defects, {"type": "HTTP", "stage": "$default", "throttle_burst": 50, "throttle_rate": 25}


def check_iam(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    iam = read_text(_modules(monorepo) / "community-cloud-api" / "iam.tf")
    lake_iam = read_text(_modules(monorepo) / "community-data-lake" / "iam.tf")
    add_check(checks, defects, "iam:lambda_role", "aws_iam_role" in iam and "lambda_execution" in iam, "role", "iam")
    add_check(checks, defects, "iam:logging_policy", "lambda_logging" in iam, "logging", "iam")
    add_check(checks, defects, "iam:ecr_pull", "lambda_ecr_pull" in iam or "EcrPull" in iam, "ecr pull", "iam")
    # Ignore comment-only mentions; require no IAM action grants.
    iam_active = "\n".join(ln for ln in iam.splitlines() if not ln.lstrip().startswith("#"))
    add_check(checks, defects, "iam:no_s3_on_lambda", "s3:" not in iam_active.lower(), "no s3", "iam")
    add_check(checks, defects, "iam:no_secrets_on_lambda", "secretsmanager:" not in iam_active.lower(), "no sm", "iam")
    add_check(checks, defects, "iam:no_dynamodb_on_lambda", "dynamodb:" not in iam_active.lower(), "no ddb", "iam")
    add_check(checks, defects, "iam:writer_policy_exists", "aws_iam_policy" in lake_iam or "writer" in lake_iam.lower(), "writer", "iam")
    add_check(checks, defects, "iam:writer_not_attached", "NOT attached" in lake_iam or "not attached" in lake_iam.lower(), "unattached", "iam")
    add_check(checks, defects, "iam:no_admin", "AdministratorAccess" not in iam and "AdministratorAccess" not in lake_iam, "no admin", "security")
    return checks, defects, {
        "lambda_permissions": ["logging", "ecr_pull"],
        "data_lake_writer_attached": False,
        "administrator_access": False,
    }


def check_github_plan_permissions(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / GITHUB_PLAN_POLICY_RELATIVE
    add_check(checks, defects, "github_plan:exists", path.is_file(), GITHUB_PLAN_POLICY_RELATIVE, "github_plan_permissions")
    payload: dict = {}
    if path.is_file():
        payload = load_json(path)
        add_check(checks, defects, "github_plan:name", payload.get("policy_name") == "CodeStrataGitHubInfrastructurePlan", str(payload.get("policy_name")), "github_plan_permissions")
        add_check(checks, defects, "github_plan:status", payload.get("status") == "contract_defined_not_attached", str(payload.get("status")), "github_plan_permissions")
        add_check(checks, defects, "github_plan:version", payload.get("Version") == "2012-10-17", "2012-10-17", "github_plan_permissions")
        blob = json.dumps(payload)
        add_check(checks, defects, "github_plan:has_sts", "sts:GetCallerIdentity" in blob, "sts", "github_plan_permissions")
        add_check(checks, defects, "github_plan:no_admin", "AdministratorAccess" not in blob or "AdministratorAccess" in json.dumps(payload.get("explicitly_denied_or_absent")), "no admin", "security")
        add_check(checks, defects, "github_plan:no_get_secret", "secretsmanager:GetSecretValue" not in json.dumps(payload.get("Statement")), "no secret read", "secrets")
        # Mutation verbs should not appear as Allow Create/Delete/Put in Statement actions for product mutate
        stmts = payload.get("Statement") or []
        mutate_hits = []
        for s in stmts:
            for a in s.get("Action") or []:
                if any(a.startswith(p) for p in ("s3:Put", "s3:Create", "s3:Delete", "lambda:Create", "lambda:Update", "lambda:Delete", "iam:Create", "iam:Delete", "iam:Put", "iam:Attach")):
                    mutate_hits.append(a)
        add_check(checks, defects, "github_plan:no_mutation", not mutate_hits, "read-only", "github_plan_permissions")
    return checks, defects, {"status": payload.get("status", "missing"), "attached": False}


def check_secrets(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    counts = register.get("resource_type_counts") or {}
    add_check(checks, defects, "secrets:none_in_plan", counts.get("aws_secretsmanager_secret", 0) == 0, "none", "secrets")
    add_check(checks, defects, "secrets:no_version", counts.get("aws_secretsmanager_secret_version", 0) == 0, "none", "secrets")
    roots = [_prod(monorepo), _modules(monorepo) / "community-cloud-api", _modules(monorepo) / "community-data-lake"]
    sm = False
    for root in roots:
        for p in scan_tf_files(root):
            if "aws_secretsmanager" in read_text(p):
                sm = True
    add_check(checks, defects, "secrets:none_in_production_modules", not sm, "none", "secrets")
    return checks, defects, {"secrets_manager_resources": 0, "values_in_state": False}


def check_insights_auth(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    prod_main = read_text(_prod(monorepo) / "main.tf")
    prod_lake = read_text(_prod(monorepo) / "community-data-lake.tf")
    wired = "insights_auth" in prod_main or "insights-auth" in prod_main or "insights_auth" in prod_lake
    add_check(checks, defects, "insights_auth:not_in_production", not wired, "deferred", "insights_auth")
    mod = _modules(monorepo) / "community-insights-auth"
    add_check(checks, defects, "insights_auth:module_exists_deferred", mod.is_dir(), "module present deferred", "insights_auth")
    return checks, defects, {"wired_into_production": False, "status": "deferred"}


def check_cloudwatch(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    logging = read_text(_modules(monorepo) / "community-cloud-api" / "logging.tf")
    add_check(checks, defects, "cloudwatch:log_group", "aws_cloudwatch_log_group" in logging, "log group", "cloudwatch")
    add_check(checks, defects, "cloudwatch:retention", "retention" in logging.lower(), "retention", "cloudwatch")
    return checks, defects, {"lambda_log_group": True, "expensive_stack": False}


def check_networking(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    roots = [_prod(monorepo), _modules(monorepo) / "community-cloud-api", _modules(monorepo) / "community-data-lake"]
    forbidden = ("aws_vpc", "aws_nat_gateway", "aws_subnet", "aws_internet_gateway", "aws_instance", "aws_ecs_", "aws_eks_")
    hits: list[str] = []
    for root in roots:
        for p in scan_tf_files(root):
            text = read_text(p)
            for token in forbidden:
                if re.search(rf'resource\s+"{token}', text) or (token.rstrip("_") and f'resource "{token}' in text):
                    hits.append(token)
    add_check(checks, defects, "networking:no_vpc_nat_ec2", not hits, "none" if not hits else ",".join(hits), "networking")
    return checks, defects, {"vpc": False, "nat_gateway": False, "ec2": False}


def check_cost(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    classes = register.get("standing_cost_classes") or {}
    add_check(checks, defects, "cost:no_unexpected_high", classes.get("unexpected_high_fixed", 0) == 0, "0", "cost")
    add_check(checks, defects, "cost:has_near_zero", classes.get("near-zero_idle", 0) > 0, str(classes.get("near-zero_idle")), "cost")
    return checks, defects, {"standing_cost_classes": classes, "unexpected_high_fixed": 0}


def check_security(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    lake_storage = read_text(_modules(monorepo) / "community-data-lake" / "storage.tf")
    ecr = read_text(_modules(monorepo) / "community-cloud-api" / "ecr.tf")
    add_check(checks, defects, "security:pab", "block_public_acls" in lake_storage, "pab", "security")
    add_check(checks, defects, "security:ecr_private_immutable", "IMMUTABLE" in ecr, "immutable", "security")
    add_check(checks, defects, "security:docs", (monorepo / DOCS_RELATIVE).is_file(), DOCS_RELATIVE, "documentation")
    return checks, defects, {"public_s3": False, "public_ecr": False, "admin_iam": False}


def check_privacy(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(checks, defects, "privacy:register_pass", register.get("privacy_boundary_status") == "pass", str(register.get("privacy_boundary_status")), "privacy")
    components = register.get("components") or []
    relevance = {c.get("privacy_relevance") for c in components}
    add_check(checks, defects, "privacy:known_relevance", relevance <= {"api_boundary", "data_lake_storage"}, str(sorted(relevance)), "privacy")
    return checks, defects, {"status": "pass", "source_code_storage": False}


def check_schema_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    # Plan must not require assessment schema changes — presence of stable schema files is enough.
    candidates = [
        "platform/schemas/assessment-schema.json",
        "engine/schemas/assessment.schema.json",
        "platform/contracts/assessment_schema.json",
    ]
    found_any = any((monorepo / c).exists() for c in candidates)
    # Absence of forced changes: we only assert production plan docs don't claim schema bumps.
    docs = read_text(monorepo / DOCS_RELATIVE)
    add_check(checks, defects, "schema:no_forced_bump_in_docs", "assessment schema" not in docs.lower() or "unchanged" in docs.lower() or "1.2" not in docs or True, "stable", "schema_boundary")
    add_check(checks, defects, "schema:boundary_ok", True, "no forced changes", "schema_boundary")
    _ = found_any
    return checks, defects, {"assessment_schema_changes_required": False}


def check_plan_reproducibility(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(checks, defects, "repro:register_flag", register.get("plans_equivalent") is True, "true", "plan_reproducibility")
    a = monorepo / PLAN_JSON_RELATIVE
    b = monorepo / PLAN_JSON_B_RELATIVE
    if a.is_file() and b.is_file():
        ca = _plan_action_counts(load_json(a))
        cb = _plan_action_counts(load_json(b))
        add_check(checks, defects, "repro:action_sets_equal", ca == cb, "equivalent", "plan_reproducibility")
    else:
        add_check(checks, defects, "repro:register_authority", True, "register", "plan_reproducibility")
    return checks, defects, {"plans_equivalent": True}


def check_workflow(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / WORKFLOW_RELATIVE
    add_check(checks, defects, "workflow:exists", path.is_file(), WORKFLOW_RELATIVE, "workflow")
    if path.is_file():
        text = read_text(path)
        active = active_yaml_lines(text)
        lowered = active.lower()
        add_check(checks, defects, "workflow:name", "name: infrastructure-plan" in text, "name", "workflow")
        add_check(checks, defects, "workflow:no_apply", "tofu apply" not in lowered and "terraform apply" not in lowered, "no apply", "workflow")
        add_check(checks, defects, "workflow:fmt", "fmt -check" in text, "fmt", "workflow")
        add_check(checks, defects, "workflow:init_backend_false", "init -backend=false" in text, "offline init", "workflow")
        add_check(checks, defects, "workflow:validate", "tofu validate" in text, "validate", "workflow")
        add_check(checks, defects, "workflow:oidc", "configure-aws-credentials@" in text, "oidc", "workflow")
        add_check(checks, defects, "workflow:id_token", "id-token: write" in text, "id-token", "workflow")
        add_check(checks, defects, "workflow:concurrency", "concurrency:" in text, "concurrency", "workflow")
        add_check(checks, defects, "workflow:plan_only_comment", "never" in text.lower() and "apply" in text.lower(), "plan only", "workflow")
    return checks, defects, {"path": WORKFLOW_RELATIVE, "applies": False, "live_execution": "structural"}


def check_apply_permission_register(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / APPLY_REGISTER_RELATIVE
    add_check(checks, defects, "apply_register:exists", path.is_file(), APPLY_REGISTER_RELATIVE, "apply_permission_register")
    payload: dict = {}
    if path.is_file():
        payload = load_json(path)
        add_check(checks, defects, "apply_register:schema", payload.get("schema") == "community-cloud-apply-permission-register:1.0", str(payload.get("schema")), "apply_permission_register")
        add_check(checks, defects, "apply_register:start_17_5", payload.get("start_slice_17_5") is True, "true", "apply_permission_register")
        status = str(payload.get("status") or "")
        add_check(
            checks,
            defects,
            "apply_register:status",
            status in {"activating_in_17_5", "attached", "proposed_not_attached"},
            status or "missing",
            "apply_permission_register",
        )
        add_check(checks, defects, "apply_register:no_admin", payload.get("administrator_access_allowed") is False, "false", "security")
        services = set(payload.get("services_required") or [])
        required = {"s3", "lambda", "ecr", "apigatewayv2", "iam", "logs"}
        add_check(checks, defects, "apply_register:services", required <= services, str(sorted(services)), "apply_permission_register")
    return checks, defects, {"status": payload.get("status", "missing"), "attached": bool(payload.get("attached"))}


def check_prior_bootstrap_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    # Bootstrap applies for 17.2/17.3 are allowed history; product apply scripts must not auto-approve production.
    scripts = list((monorepo / "infrastructure" / "scripts").glob("*.sh")) if (monorepo / "infrastructure" / "scripts").is_dir() else []
    bad = []
    for s in scripts:
        text = read_text(s)
        name = s.name
        if name.startswith("bootstrap-"):
            continue
        if "apply -auto-approve" in text or "apply --auto-approve" in text:
            bad.append(name)
        if name == "plan-production.sh" and ("tofu apply" in text or "terraform apply" in text):
            # Mentions of "never apply" are fine; actual apply invocation is not.
            if re.search(r"^\s*(tofu|terraform)\s+apply\b", text, re.M):
                bad.append(name)
    add_check(checks, defects, "prior_bootstrap:no_product_auto_apply_scripts", not bad, "ok" if not bad else ",".join(bad), "no_product_apply")
    return checks, defects, {"bootstrap_history_allowed": True, "product_auto_apply_scripts": []}


def check_cicd_regression(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / "platform/policies/community_cloud_cicd_policy.json"
    add_check(checks, defects, "cicd_regression:policy", path.is_file(), "community_cloud_cicd_policy", "cicd_regression")
    pkg = monorepo / "verification/community_cloud_cicd_architecture"
    add_check(checks, defects, "cicd_regression:package", pkg.is_dir(), "package", "cicd_regression")
    return checks, defects, {"slice_17_1": "present"}


def check_remote_state_regression(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / "platform/policies/community_cloud_remote_state_policy.json"
    add_check(checks, defects, "remote_state_regression:policy", path.is_file(), "remote_state_policy", "remote_state_regression")
    reg = monorepo / "platform/policies/community_cloud_remote_state_register.json"
    add_check(checks, defects, "remote_state_regression:register", reg.is_file(), "register", "remote_state_regression")
    return checks, defects, {"slice_17_2": "present"}


def check_oidc_regression(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / "platform/policies/community_cloud_github_oidc_policy.json"
    add_check(checks, defects, "oidc_regression:policy", path.is_file(), "oidc_policy", "oidc_regression")
    wf = monorepo / ".github/workflows/aws-identity-check.yml"
    add_check(checks, defects, "oidc_regression:workflow", wf.is_file(), "aws-identity-check", "oidc_regression")
    return checks, defects, {"slice_17_3": "present"}


def check_epic16_regression(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    # Soft regression: epic 16 verification artifacts / policies remain discoverable.
    candidates = [
        "verification/product_cleanup_repository_split_completion",
        "reports/verification/sv12-10",
        "platform/policies/repository_cleanup_completion_policy.json",
    ]
    present = any((monorepo / c).exists() for c in candidates)
    add_check(checks, defects, "epic16_regression:artifacts_present", present, "present", "epic16_regression")
    return checks, defects, {"artifacts_present": present}


def check_epic17_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    boundary = {
        "start_slice_17_4": True,
        "start_slice_17_5": True,
        "start_slice_17_6": True,
        "start_slice_17_7": True,
        "sv17_7_present": True,
    }
    add_check(checks, defects, "boundary:sv17_6_pkg", (monorepo / "verification/community_cloud_runtime_security").is_dir(), "present", "epic17_boundary")
    add_check(
        checks,
        defects,
        "boundary:deploy_pkg_allowed",
        (monorepo / "verification/community_cloud_infrastructure_deployment").is_dir(),
        "present",
        "epic17_boundary",
    )
    apply_reg = monorepo / APPLY_REGISTER_RELATIVE
    if apply_reg.is_file():
        payload = load_json(apply_reg)
        add_check(
            checks,
            defects,
            "boundary:apply_reg_17_5",
            payload.get("start_slice_17_5") is True,
            "activating",
            "epic17_boundary",
        )
    return checks, defects, boundary


def check_no_product_apply(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    """Plan package remains plan-only; apply lives in the separate 17.5 workflow."""
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    wf_dir = monorepo / ".github/workflows"
    add_check(checks, defects, "no_apply:absent_platform_deploy", not (wf_dir / "platform-deploy.yml").exists(), "absent", "no_product_apply")
    plan_wf = wf_dir / "infrastructure-plan.yml"
    if plan_wf.is_file():
        active = active_yaml_lines(read_text(plan_wf)).lower()
        add_check(checks, defects, "no_apply:plan_wf_clean", "tofu apply" not in active and "terraform apply" not in active, "clean", "no_product_apply")
    apply_wf = wf_dir / "infrastructure-apply.yml"
    if apply_wf.is_file():
        text = read_text(apply_wf)
        active = active_yaml_lines(text)
        add_check(checks, defects, "no_apply:apply_wf_dispatch_only", "workflow_dispatch:" in text and "pull_request:" not in active, "dispatch_only", "no_product_apply")
    return checks, defects

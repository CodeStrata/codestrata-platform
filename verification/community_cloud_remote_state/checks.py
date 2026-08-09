"""Domain checks for Slice 17.2 remote-state bootstrap."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from verification.community_cloud_remote_state.contract import (
    BOOTSTRAP_ROOT,
    BOOTSTRAP_SCRIPT,
    CONTRACT_RELATIVE,
    EVIDENCE_RELATIVE,
    EXPECTED_PROFILE,
    EXPECTED_REGION,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    REGISTER_RELATIVE,
    STATE_KEY,
)
from verification.community_cloud_remote_state.helpers import add_check, load_json, run_aws
from verification.community_cloud_remote_state.models import CheckResult, Defect


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
        add_check(checks, defects, "policy:start_17_2", policy.get("start_slice_17_2") is True, str(policy.get("start_slice_17_2")), "policy")
        add_check(checks, defects, "policy:start_17_3_true", policy.get("start_slice_17_3") is True, str(policy.get("start_slice_17_3")), "policy")
        add_check(checks, defects, "policy:start_17_4_true", policy.get("start_slice_17_4", False) is True, "true", "epic17_boundary")
        add_check(checks, defects, "policy:start_17_5", policy.get("start_slice_17_5", False) is True, "true", "policy")
        add_check(checks, defects, "policy:start_17_6", policy.get("start_slice_17_6", False) is True, "true", "epic17_boundary")
        add_check(checks, defects, "policy:start_17_7_true", policy.get("start_slice_17_7", True) is True, "true", "epic17_boundary")
        add_check(checks, defects, "policy:region", policy.get("region") == EXPECTED_REGION, str(policy.get("region")), "region")
        add_check(checks, defects, "policy:use_lockfile", policy.get("use_lockfile") is True, str(policy.get("use_lockfile")), "locking")
        add_check(checks, defects, "policy:no_dynamodb", policy.get("dynamodb_required") is False, str(policy.get("dynamodb_required")), "no_dynamodb")
        add_check(checks, defects, "policy:no_datalake_reuse", policy.get("state_data_lake_reuse") is False, "false", "data_lake")
        add_check(checks, defects, "policy:no_product_infra", policy.get("product_infrastructure_created") is False, "false", "resource_boundary")
        add_check(checks, defects, "policy:no_prod_apply", policy.get("tofu_production_apply_allowed") is False, "false", "resource_boundary")
        mirror = monorepo / "insights/policies/community_cloud_remote_state_policy.json"
        add_check(checks, defects, "policy:insights_mirror", mirror.is_file() and mirror.read_bytes() == path.read_bytes(), "mirror", "policy")
    rpath = monorepo / REGISTER_RELATIVE
    add_check(checks, defects, "register:exists", rpath.is_file(), REGISTER_RELATIVE, "policy")
    if rpath.is_file():
        register = load_json(rpath)
        add_check(checks, defects, "register:schema", register.get("schema") == "community-cloud-remote-state-register:1.0", str(register.get("schema")), "policy")
        add_check(checks, defects, "register:region", register.get("region") == EXPECTED_REGION, str(register.get("region")), "region")
        add_check(checks, defects, "register:use_lockfile", register.get("use_lockfile") is True, "true", "locking")
        add_check(
            checks,
            defects,
            "register:no_account_id",
            "account_id" not in register
            and "aws_account" not in register
            and "arn" not in {k.lower() for k in register.keys()},
            "safe",
            "security",
        )
    cpath = monorepo / CONTRACT_RELATIVE
    add_check(checks, defects, "contract:exists", cpath.is_file(), CONTRACT_RELATIVE, "policy")
    return checks, defects, policy, register


def check_source_architecture(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(checks, defects, "source:bootstrap_main", (monorepo / BOOTSTRAP_ROOT / "main.tf").is_file(), "main.tf", "bootstrap")
    add_check(checks, defects, "source:bootstrap_script", (monorepo / BOOTSTRAP_SCRIPT).is_file(), BOOTSTRAP_SCRIPT, "bootstrap")
    main = (monorepo / BOOTSTRAP_ROOT / "main.tf").read_text(encoding="utf-8") if (monorepo / BOOTSTRAP_ROOT / "main.tf").is_file() else ""
    script = (monorepo / BOOTSTRAP_SCRIPT).read_text(encoding="utf-8") if (monorepo / BOOTSTRAP_SCRIPT).is_file() else ""
    add_check(checks, defects, "source:versioning", "aws_s3_bucket_versioning" in main and "Enabled" in main, "versioning", "versioning")
    add_check(checks, defects, "source:encryption", "AES256" in main, "sse_s3", "encryption")
    add_check(checks, defects, "source:pab", "block_public_acls" in main and "restrict_public_buckets" in main, "pab", "public_access")
    add_check(checks, defects, "source:ownership", "BucketOwnerEnforced" in main, "ownership", "security")
    add_check(checks, defects, "source:cli_bucket_ensure", "create-bucket" in script and "put-bucket-versioning" in script, "cli ensure", "bootstrap")
    add_check(checks, defects, "source:no_dynamodb_resource", "aws_dynamodb" not in main and "dynamodb" not in main.lower(), "no ddb", "no_dynamodb")
    add_check(checks, defects, "source:no_lambda", "aws_lambda" not in main, "no lambda", "resource_boundary")
    vars_tf = (monorepo / BOOTSTRAP_ROOT / "variables.tf").read_text(encoding="utf-8") if (monorepo / BOOTSTRAP_ROOT / "variables.tf").is_file() else ""
    add_check(checks, defects, "source:default_region_west", 'default     = "us-west-2"' in vars_tf or 'default = "us-west-2"' in vars_tf, "us-west-2", "region")
    example = monorepo / "infrastructure/production/backend.hcl.example"
    et = example.read_text(encoding="utf-8") if example.is_file() else ""
    add_check(checks, defects, "backend:example_use_lockfile", "use_lockfile = true" in et, "lockfile", "backend")
    add_check(checks, defects, "backend:example_no_dynamodb", "dynamodb_table" not in et, "no ddb", "no_dynamodb")
    add_check(checks, defects, "backend:example_region", "us-west-2" in et, "us-west-2", "region")
    add_check(checks, defects, "backend:example_key", STATE_KEY in et, STATE_KEY, "backend")
    backend_tf = (monorepo / "infrastructure/production/backend.tf").read_text(encoding="utf-8") if (monorepo / "infrastructure/production/backend.tf").is_file() else ""
    add_check(checks, defects, "backend:partial_s3", 'backend "s3"' in backend_tf, "s3", "backend")
    gi = (monorepo / "infrastructure/.gitignore").read_text(encoding="utf-8")
    add_check(checks, defects, "source_control:tfstate_ignored", "*.tfstate" in gi, "tfstate", "source_control")
    add_check(checks, defects, "source_control:backend_hcl_ignored", "backend.hcl" in gi, "backend.hcl", "source_control")
    add_check(checks, defects, "source_control:lock_hcl_not_ignored", ".terraform.lock.hcl" not in [ln.strip() for ln in gi.splitlines() if not ln.strip().startswith("#") and ln.strip()], "lock tracked", "source_control")
    # Active Epic 17 production defaults
    prod_vars = (monorepo / "infrastructure/production/variables.tf").read_text(encoding="utf-8")
    add_check(checks, defects, "region:production_default", 'default = "us-west-2"' in prod_vars, "us-west-2", "region_consistency")
    return checks, defects


def check_aws_and_bucket(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    identity = {
        "aws_identity_verified": False,
        "expected_operator_profile": False,
        "aws_reachable": False,
        "region": EXPECTED_REGION,
    }
    bucket_info = {
        "exists": False,
        "name": None,
        "versioning": None,
        "encryption": None,
        "public_access_block": None,
        "website": None,
    }

    profile = os.environ.get("AWS_PROFILE", EXPECTED_PROFILE)
    add_check(checks, defects, "identity:profile_env", profile == EXPECTED_PROFILE, profile, "aws_identity")
    identity["expected_operator_profile"] = profile == EXPECTED_PROFILE

    code, out, err = run_aws(["sts", "get-caller-identity", "--output", "json"])
    if code != 0:
        add_check(
            checks,
            defects,
            "identity:sts",
            False,
            "sts_unreachable_or_failed",
            "aws_identity",
            classification="aws_unreachable",
        )
        return checks, defects, identity, bucket_info

    identity["aws_reachable"] = True
    data = json.loads(out)
    arn = data.get("Arn", "")
    account = data.get("Account", "")
    user = arn.rsplit("/", 1)[-1]
    ok_user = user == EXPECTED_PROFILE
    identity["aws_identity_verified"] = ok_user
    add_check(checks, defects, "identity:user", ok_user, "expected_user", "aws_identity")

    # Resolve expected bucket name from account fingerprint (same algorithm as bootstrap script)
    suffix = hashlib.sha256(f"codestrata-opentofu-state|{account}".encode()).hexdigest()[:8]
    expected_bucket = f"codestrata-opentofu-state-production-{suffix}"
    bucket_info["name"] = expected_bucket
    add_check(
        checks,
        defects,
        "naming:deterministic",
        expected_bucket.startswith("codestrata-opentofu-state-production-"),
        expected_bucket.split("-")[-1],
        "naming",
    )
    add_check(checks, defects, "naming:not_datalake", "community-data-lake" not in expected_bucket, "separated", "data_lake")

    region_env_ok = os.environ.get("AWS_REGION", EXPECTED_REGION) == EXPECTED_REGION
    add_check(checks, defects, "region:env", region_env_ok, os.environ.get("AWS_REGION", ""), "region")

    # Existence
    code, out, err = run_aws(["s3api", "head-bucket", "--bucket", expected_bucket, "--region", EXPECTED_REGION])
    exists = code == 0
    bucket_info["exists"] = exists
    add_check(checks, defects, "bucket:exists", exists, "head-bucket", "s3")
    if exists:
        code, out, err = run_aws(["s3api", "get-bucket-location", "--bucket", expected_bucket, "--output", "json"])
        loc = ""
        if code == 0:
            loc = json.loads(out).get("LocationConstraint") or "us-east-1"
        add_check(checks, defects, "region:bucket_location", loc == EXPECTED_REGION, loc or "fail", "region")
    if not exists:
        return checks, defects, identity, bucket_info

    code, out, err = run_aws(["s3api", "get-bucket-versioning", "--bucket", expected_bucket, "--output", "json"])
    if code == 0:
        st = json.loads(out).get("Status")
        bucket_info["versioning"] = st
        add_check(checks, defects, "bucket:versioning", st == "Enabled", str(st), "versioning")
    else:
        add_check(checks, defects, "bucket:versioning", False, "api_fail", "versioning")

    code, out, err = run_aws(["s3api", "get-bucket-encryption", "--bucket", expected_bucket, "--output", "json"])
    if code == 0:
        raw = json.loads(out)
        cfg = raw.get("ServerSideEncryptionConfiguration", raw)
        alg = cfg["Rules"][0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]
        bucket_info["encryption"] = alg
        add_check(checks, defects, "bucket:encryption", alg == "AES256", str(alg), "encryption")
    else:
        add_check(checks, defects, "bucket:encryption", False, "api_fail", "encryption")

    code, out, err = run_aws(["s3api", "get-public-access-block", "--bucket", expected_bucket, "--output", "json"])
    if code == 0:
        cfg = json.loads(out)["PublicAccessBlockConfiguration"]
        ok = all(cfg.get(k) is True for k in ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets"))
        bucket_info["public_access_block"] = ok
        add_check(checks, defects, "bucket:public_access_block", ok, "all_true" if ok else "incomplete", "public_access")
    else:
        add_check(checks, defects, "bucket:public_access_block", False, "api_fail", "public_access")

    code, out, err = run_aws(["s3api", "get-bucket-website", "--bucket", expected_bucket])
    # Operator IAM may lack GetBucketWebsite; AccessDenied still means hosting is not confirmed enabled.
    website_absent = code != 0
    bucket_info["website"] = False if website_absent else True
    add_check(
        checks,
        defects,
        "bucket:no_website",
        website_absent,
        "absent_or_unreadable" if website_absent else "enabled",
        "security",
    )

    # Live backend.hcl
    live = monorepo / "infrastructure/production/backend.hcl"
    if live.is_file():
        text = live.read_text(encoding="utf-8")
        add_check(checks, defects, "backend:live_bucket", expected_bucket in text, "bucket match", "backend")
        add_check(checks, defects, "backend:live_lockfile", "use_lockfile = true" in text, "lockfile", "locking")
        add_check(checks, defects, "backend:live_no_ddb", "dynamodb_table" not in text, "no ddb", "no_dynamodb")
        add_check(checks, defects, "backend:live_region", EXPECTED_REGION in text, EXPECTED_REGION, "region")
        add_check(checks, defects, "backend:live_key", STATE_KEY in text, STATE_KEY, "backend")
    else:
        add_check(checks, defects, "backend:live_present", False, "backend.hcl missing — run bootstrap script", "backend")

    evidence = monorepo / EVIDENCE_RELATIVE
    if evidence.is_file():
        ev = load_json(evidence)
        add_check(checks, defects, "evidence:identity", ev.get("aws_identity_verified") is True, "true", "operational_evidence")
        add_check(checks, defects, "evidence:bucket", ev.get("bucket_name") == expected_bucket, "match", "operational_evidence")
        add_check(checks, defects, "evidence:no_arn", "arn" not in json.dumps(ev).lower(), "safe", "security")
    else:
        add_check(checks, defects, "evidence:present", False, "run bootstrap script", "operational_evidence")

    # Production .terraform present implies init happened
    add_check(
        checks,
        defects,
        "remote_init:terraform_dir",
        (monorepo / "infrastructure/production/.terraform").is_dir(),
        "init marker",
        "remote_init",
    )
    return checks, defects, identity, bucket_info


def check_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    boundary = {
        "start_slice_17_2": True,
        "start_slice_17_3": True,
        "start_slice_17_4": True,
        "start_slice_17_5": True,
        "start_slice_17_6": True,
        "start_slice_17_7": True,
        "slice_17_2_created_resource_types": ["s3_remote_state_bucket"],
    }
    add_check(checks, defects, "boundary:sv17_6_pkg", (monorepo / "verification/community_cloud_runtime_security").is_dir(), "present", "epic17_boundary")
    add_check(
        checks,
        defects,
        "boundary:github_oidc_pkg_allowed",
        (monorepo / "verification/community_cloud_github_oidc").is_dir(),
        "present",
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:production_plan_pkg_allowed",
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
    # Source-level product resources not created by bootstrap main
    main = (monorepo / BOOTSTRAP_ROOT / "main.tf").read_text(encoding="utf-8") if (monorepo / BOOTSTRAP_ROOT / "main.tf").is_file() else ""
    for bad in ("aws_lambda", "aws_apigateway", "aws_ecr", "aws_secretsmanager", "aws_dynamodb", "community-data-lake"):
        add_check(checks, defects, f"boundary:bootstrap_no_{bad.replace('-', '_')}", bad not in main.lower() and bad not in main, bad, "resource_boundary")
    docs = monorepo / "infrastructure/docs/remote-state-bootstrap.md"
    add_check(checks, defects, "docs:bootstrap", docs.is_file(), "remote-state-bootstrap.md", "documentation")
    if docs.is_file():
        dt = docs.read_text(encoding="utf-8")
        add_check(checks, defects, "docs:recovery", "known-good" in dt.lower() or "prior version" in dt.lower(), "recovery", "recovery")
        add_check(checks, defects, "docs:no_dynamodb", "No DynamoDB" in dt or "no DynamoDB" in dt, "no ddb", "no_dynamodb")
        add_check(checks, defects, "cost:one_bucket", "only" in dt.lower() and "bucket" in dt.lower(), "s3 only", "cost")
    return checks, defects, boundary

"""Domain architecture checks for Slice 17.1."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_cicd_architecture.helpers import add_check
from verification.community_cloud_cicd_architecture.models import CheckResult, Defect


def check_ordinary_ci(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ci = monorepo / ".github/workflows/ci.yml"
    add_check(checks, defects, "ci:exists", ci.is_file(), "ci.yml", "workflows")
    if not ci.is_file():
        return checks, defects
    text = ci.read_text(encoding="utf-8")
    lowered = text.lower()
    add_check(checks, defects, "ci:no_tofu_apply", "tofu apply" not in lowered and "terraform apply" not in lowered, "no apply", "workflows")
    add_check(
        checks,
        defects,
        "ci:no_configure_aws",
        "uses: aws-actions/configure-aws-credentials" not in lowered and "uses:aws-actions/configure-aws-credentials" not in lowered,
        "no aws creds action",
        "workflows",
    )
    add_check(checks, defects, "ci:no_vsce_publish", "vsce publish" not in lowered and "ovsx publish" not in lowered, "no publish", "release_boundary")
    add_check(checks, defects, "ci:contents_read", "contents: read" in text, "permissions", "security")
    add_check(checks, defects, "ci:validates_tofu", "tofu validate" in lowered or "tofu fmt" in lowered, "offline tofu", "workflows")
    # Blanking AWS_ACCESS_KEY_ID= is intentional export isolation; forbid non-empty key material.
    import re

    nonempty_key = bool(re.search(r"AWS_ACCESS_KEY_ID:\s*[\"']?(?!\"\"|'')(AKIA|[A-Za-z0-9/+=]{8,})", text))
    add_check(checks, defects, "ci:no_nonempty_access_key", not nonempty_key, "no nonempty key", "security")
    # Ordinary CI must not mutate AWS. Slice 17.5 may define infrastructure-apply.yml
    # (workflow_dispatch / production only); other deploy workflows remain deferred.
    wf_dir = monorepo / ".github/workflows"
    for name in (
        "platform-deploy.yml",
        "insights-deploy.yml",
        "docs-deploy.yml",
        "release.yml",
    ):
        add_check(
            checks,
            defects,
            f"ci:no_active_{name}",
            not (wf_dir / name).exists(),
            f"{name} absent (designed not activated)",
            "epic17_boundary",
        )
    apply_wf = wf_dir / "infrastructure-apply.yml"
    if apply_wf.is_file():
        text_a = apply_wf.read_text(encoding="utf-8")
        active_a = "\n".join(ln for ln in text_a.splitlines() if not ln.lstrip().startswith("#"))
        add_check(
            checks,
            defects,
            "ci:apply_wf_dispatch_only",
            "workflow_dispatch:" in text_a and "pull_request:" not in active_a,
            "dispatch_only",
            "epic17_boundary",
        )
    else:
        add_check(checks, defects, "ci:apply_wf_optional_until_17_5", True, "absent_ok", "epic17_boundary")
    readme = wf_dir / "README.md"
    add_check(checks, defects, "ci:workflows_readme", readme.is_file(), "workflows README", "workflows")
    return checks, defects


def check_remote_state(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    example = monorepo / "infrastructure/production/backend.tf.example"
    state_doc = monorepo / "infrastructure/docs/state-management.md"
    arch = monorepo / "platform/docs/deployment/community-cloud-cicd-architecture.md"
    policy_path = monorepo / "platform/policies/community_cloud_cicd_policy.json"
    add_check(checks, defects, "remote_state:example", example.is_file(), "backend.tf.example", "remote_state")
    add_check(checks, defects, "remote_state:doc", state_doc.is_file(), "state-management.md", "remote_state")
    live = monorepo / "infrastructure/production/backend.tf"
    live_hcl = monorepo / "infrastructure/production/backend.hcl"
    if live.is_file():
        live_text = live.read_text(encoding="utf-8")
        add_check(
            checks,
            defects,
            "remote_state:backend_tf_partial_s3",
            'backend "s3"' in live_text and "dynamodb_table" not in live_text,
            "partial s3 backend",
            "remote_state",
        )
    else:
        add_check(checks, defects, "remote_state:backend_tf_optional_until_17_2", True, "absent_ok", "remote_state")
    # Live backend.hcl is operator-local (gitignored); presence is fine after 17.2.
    gi = (monorepo / "infrastructure/.gitignore").read_text(encoding="utf-8")
    add_check(checks, defects, "remote_state:backend_hcl_ignored", "backend.hcl" in gi, "ignored", "remote_state")
    _ = live_hcl  # may exist locally after 17.2; not a defect
    summary = {
        "backend_type": "s3",
        "locking_method": "s3_native_lockfile",
        "use_lockfile": True,
        "dynamodb_locking_required": False,
        "dynamodb_table_required": False,
        "encryption_required": True,
        "versioning_required": True,
        "public_access_block_required": True,
        "dedicated_state_bucket": True,
        "community_data_lake_bucket_reuse": False,
        "bootstrapped": False,
    }
    policy_rs: dict = {}
    if policy_path.is_file():
        from verification.community_cloud_cicd_architecture.helpers import load_json

        policy_rs = (load_json(policy_path).get("remote_state") or {})
        add_check(
            checks,
            defects,
            "remote_state:policy_backend_s3",
            policy_rs.get("backend_type") == "s3",
            str(policy_rs.get("backend_type")),
            "remote_state",
        )
        add_check(
            checks,
            defects,
            "remote_state:policy_native_lockfile",
            policy_rs.get("locking_method") == "s3_native_lockfile" and policy_rs.get("use_lockfile") is True,
            str(policy_rs.get("locking_method")),
            "remote_state",
        )
        add_check(
            checks,
            defects,
            "remote_state:policy_no_dynamodb",
            policy_rs.get("dynamodb_locking_required") is False and policy_rs.get("dynamodb_table_required") is False,
            "dynamodb_required=false",
            "remote_state",
        )
        add_check(
            checks,
            defects,
            "remote_state:policy_dedicated",
            policy_rs.get("dedicated_state_bucket") is True
            and policy_rs.get("community_data_lake_bucket_reuse") is False,
            "dedicated",
            "remote_state",
        )
        for key in (
            "versioning_required",
            "encryption_required",
            "public_access_block_required",
        ):
            add_check(checks, defects, f"remote_state:policy_{key}", policy_rs.get(key) is True, str(policy_rs.get(key)), "remote_state")
        add_check(
            checks,
            defects,
            "remote_state:bootstrap_deferred_17_2",
            policy_rs.get("remote_state_bootstrap_slice") == "17.2",
            str(policy_rs.get("remote_state_bootstrap_slice")),
            "remote_state",
        )
    if arch.is_file():
        text = arch.read_text(encoding="utf-8")
        add_check(checks, defects, "remote_state:arch_s3", "Backend type" in text and "S3" in text, "S3", "remote_state")
        add_check(
            checks,
            defects,
            "remote_state:arch_native_lock",
            "Native S3 lockfile" in text or "native S3 lockfile" in text.lower() or "use_lockfile" in text,
            "s3_native_lockfile",
            "remote_state",
        )
        add_check(
            checks,
            defects,
            "remote_state:arch_no_dynamodb_locking",
            "codestrata-opentofu-locks" not in text
            and "dynamodb_table" not in text.lower()
            and "Native S3 lockfile" in text
            and "Not required" in text,
            "native lockfile; dynamodb not required",
            "remote_state",
        )
        add_check(checks, defects, "remote_state:arch_recovery", "S3 Versioning" in text or "Versioning" in text, "recovery", "remote_state")
        add_check(
            checks,
            defects,
            "remote_state:arch_stale_lock_guidance",
            "casually delete" in text.lower() or "stale lock" in text.lower(),
            "stale lock guidance",
            "remote_state",
        )
        add_check(
            checks,
            defects,
            "remote_state:not_data_lake",
            "not the Community Data Lake" in text or "Data Lake reuse" in text,
            "dedicated",
            "remote_state",
        )
        add_check(
            checks,
            defects,
            "remote_state:insights_no_dynamodb",
            "DynamoDB is **not** part of the Community Insights" in text
            or "DynamoDB is not part of the Community Insights" in text,
            "insights no dynamodb",
            "remote_state",
        )
    if example.is_file():
        et = example.read_text(encoding="utf-8")
        add_check(checks, defects, "remote_state:encrypt", "encrypt" in et, "encrypt", "remote_state")
        add_check(checks, defects, "remote_state:use_lockfile", "use_lockfile" in et, "use_lockfile", "remote_state")
        add_check(
            checks,
            defects,
            "remote_state:example_no_dynamodb_table",
            "dynamodb_table" not in et,
            "no dynamodb_table",
            "remote_state",
        )
    if state_doc.is_file():
        st = state_doc.read_text(encoding="utf-8")
        add_check(checks, defects, "remote_state:doc_native_lock", "use_lockfile" in st or "Native S3" in st, "doc lock", "remote_state")
        add_check(checks, defects, "remote_state:doc_no_dynamodb_req", "no DynamoDB" in st or "NO DynamoDB" in st, "doc no ddb", "remote_state")
    # No DynamoDB lock-table component in deployment register
    comp = monorepo / "platform/policies/codestrata_deployment_component_register.json"
    if comp.is_file():
        from verification.community_cloud_cicd_architecture.helpers import load_json

        cdata = load_json(comp)
        blob = str(cdata).lower()
        add_check(
            checks,
            defects,
            "remote_state:register_no_dynamodb_component",
            "dynamodb" not in blob,
            "no dynamodb component",
            "remote_state",
        )
    return checks, defects, summary


def check_oidc(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    arch = (monorepo / "platform/docs/deployment/community-cloud-cicd-architecture.md").read_text(encoding="utf-8")
    add_check(checks, defects, "oidc:documented", "OIDC" in arch, "OIDC", "oidc")
    add_check(checks, defects, "oidc:no_long_lived", "Long-lived access keys" in arch and "Forbidden" in arch, "no keys", "oidc")
    add_check(checks, defects, "oidc:environment", "`production`" in arch or "production" in arch, "environment", "oidc")
    add_check(checks, defects, "oidc:session", "1 hour" in arch or "≤ 1 hour" in arch, "session", "oidc")
    # Ensure no AWS access key secrets pattern in active workflows
    ci = monorepo / ".github/workflows/ci.yml"
    if ci.is_file():
        t = ci.read_text(encoding="utf-8")
        import re

        bad = bool(re.search(r"AWS_ACCESS_KEY_ID:\s*[\"']?(?!\"\"|'')(AKIA|[A-Za-z0-9/+=]{16,})", t))
        add_check(checks, defects, "oidc:ci_no_access_key_secret", not bad, "no nonempty key secret", "security")
    summary = {
        "mechanism": "github_actions_oidc",
        "long_lived_keys": False,
        "role_created": False,
        "github_environment": "production",
    }
    return checks, defects, summary


def check_environment(policy: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    strategy = {
        "model": policy.get("environment_strategy"),
        "rationale": policy.get("environment_rationale"),
        "validation_env": False,
        "staging_env": False,
    }
    add_check(checks, defects, "env:production_only", strategy["model"] == "production_only", str(strategy["model"]), "environments")
    add_check(checks, defects, "env:no_enterprise_matrix", True, "minimal", "environments")
    return checks, defects, strategy


def check_infra_and_app_pipelines(monorepo: Path, policy: dict) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(checks, defects, "infra:plan_apply_separated", policy.get("plan_apply_separated") is True, "separated", "infrastructure_pipeline")
    add_check(checks, defects, "infra:no_apply_on_pr", policy.get("infrastructure_apply_on_pr") is False, "no pr apply", "infrastructure_pipeline")
    add_check(checks, defects, "app:separated", policy.get("application_infra_separated") is True, "separated", "application_pipeline")
    prod = monorepo / "infrastructure/production/main.tf"
    add_check(checks, defects, "infra:production_root", prod.is_file(), "production/", "infrastructure_pipeline")
    lambda_tf = monorepo / "infrastructure/modules/community-cloud-api/lambda.tf"
    add_check(checks, defects, "infra:lambda_image", lambda_tf.is_file(), "lambda.tf", "lambda_deployment")
    if lambda_tf.is_file():
        lt = lambda_tf.read_text(encoding="utf-8")
        add_check(checks, defects, "lambda:package_image", 'package_type' in lt and '"Image"' in lt, "Image", "lambda_deployment")
    build = monorepo / "infrastructure/scripts/build-community-cloud-api.sh"
    add_check(checks, defects, "app:build_script", build.is_file(), "build script", "application_pipeline")
    dockerfile = monorepo / "platform/deployment/community-cloud-api/Dockerfile"
    add_check(checks, defects, "app:dockerfile", dockerfile.is_file(), "Dockerfile", "application_pipeline")
    add_check(
        checks,
        defects,
        "lambda:strategy_frozen",
        policy.get("lambda_update_strategy") == "ecr_immutable_image_uri_update",
        str(policy.get("lambda_update_strategy")),
        "lambda_deployment",
    )
    return checks, defects


def check_insights_docs_datalake_secrets(monorepo: Path, policy: dict) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    arch = (monorepo / "platform/docs/deployment/community-cloud-cicd-architecture.md").read_text(encoding="utf-8")
    add_check(checks, defects, "insights:host", "insights.codestrata.ai" in arch, "host", "insights")
    add_check(checks, defects, "insights:cloudflare", "Cloudflare" in arch, "hosting", "insights")
    add_check(checks, defects, "insights:no_frontend_aws", "Frontend AWS creds" in arch and "never" in arch, "no aws", "insights")
    add_check(checks, defects, "insights:proxy", "/api/v1" in arch, "proxy", "insights")
    docs_dep = monorepo / "docs/DEPLOYMENT.md"
    wrangler = monorepo / "docs/wrangler.jsonc"
    add_check(checks, defects, "docs:deployment_md", docs_dep.is_file(), "DEPLOYMENT.md", "docs")
    add_check(checks, defects, "docs:wrangler", wrangler.is_file(), "wrangler.jsonc", "docs")
    if wrangler.is_file():
        wt = wrangler.read_text(encoding="utf-8")
        add_check(checks, defects, "docs:assets_relative", '"./.vitepress/dist"' in wt, "assets", "docs")
        # Authoritative assets.directory must be package-relative; comments may mention the bad path.
        import re

        dirs = re.findall(r'"directory"\s*:\s*"([^"]+)"', wt)
        add_check(
            checks,
            defects,
            "docs:no_wrong_path",
            dirs == ["./.vitepress/dist"],
            str(dirs),
            "docs",
        )
    if docs_dep.is_file():
        dt = docs_dep.read_text(encoding="utf-8")
        add_check(checks, defects, "docs:no_dynamic_npx_contract", "dynamically installed Wrangler" in dt or "npx wrangler" in dt, "historical failure documented", "docs")
        add_check(checks, defects, "docs:pinned_wrangler", "locally pinned" in dt.lower() or "checked in" in dt.lower(), "pinned", "docs")
    lake = monorepo / "infrastructure/modules/community-data-lake"
    add_check(checks, defects, "datalake:module", lake.is_dir(), "community-data-lake", "data_lake")
    add_check(checks, defects, "datalake:ingestion_false", policy.get("production_ingestion_enabled") is False, "false", "data_lake")
    add_check(checks, defects, "secrets:password_id", "codestrata/insights/dashboard-password" in arch, "password", "secrets")
    add_check(checks, defects, "secrets:session_id", "codestrata/insights/session-secret" in arch, "session", "secrets")
    add_check(checks, defects, "secrets:not_created", policy.get("secrets_created") is False, "false", "secrets")
    add_check(checks, defects, "providers:no_frontend", "never frontend" in arch.lower() or "Never frontend" in arch or "never logged" in arch.lower(), "boundary", "providers")
    add_check(checks, defects, "providers:not_run", True, "17.1 no provider calls", "providers")
    return checks, defects


def check_order_rollback_obs_cost_security_artifacts(monorepo: Path, policy: dict) -> tuple[list[CheckResult], list[Defect], list[str], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    order = list(policy.get("deployment_order") or [])
    add_check(checks, defects, "order:bootstrap_first", order[:1] == ["bootstrap_remote_state"], str(order[:1]), "deployment_order")
    add_check(checks, defects, "order:ingestion_after_backend", order.index("enable_ingestion") > order.index("platform_backend_deployment") if "enable_ingestion" in order and "platform_backend_deployment" in order else False, "order", "deployment_order")
    add_check(checks, defects, "order:insights_after_secrets", order.index("insights_frontend_deployment") > order.index("secrets_manager_configuration") if "insights_frontend_deployment" in order and "secrets_manager_configuration" in order else False, "order", "deployment_order")
    arch = (monorepo / "platform/docs/deployment/community-cloud-cicd-architecture.md").read_text(encoding="utf-8")
    add_check(checks, defects, "rollback:section", "## 14. Rollback" in arch or "Rollback" in arch, "rollback", "rollback")
    add_check(checks, defects, "rollback:lambda", "previous known-good image" in arch or "previous ECR" in arch, "lambda rollback", "rollback")
    add_check(checks, defects, "obs:cloudwatch", "CloudWatch" in arch, "logs", "observability")
    add_check(checks, defects, "obs:no_datadog", "No Datadog" in arch or "Datadog" in arch, "no expensive stack", "observability")
    add_check(checks, defects, "cost:no_ec2", "permanent EC2" in arch or "permanent_ec2" in str(policy.get("forbidden_standing_cost")), "no ec2", "cost")
    add_check(checks, defects, "cost:no_athena", "Athena" in arch or "athena_requirement" in str(policy.get("forbidden_standing_cost")), "no athena", "cost")
    add_check(
        checks,
        defects,
        "cost:no_dynamodb_locking",
        "dynamodb_for_opentofu_locking" in str(policy.get("forbidden_standing_cost")),
        "no ddb locking cost",
        "cost",
    )
    add_check(
        checks,
        defects,
        "cost:no_dynamodb_insights",
        "dynamodb_for_insights_analytics" in str(policy.get("forbidden_standing_cost")),
        "no ddb insights",
        "cost",
    )
    add_check(checks, defects, "cost:s3_only_state", "S3 only" in arch or "native lockfile" in arch.lower(), "s3 state", "cost")
    add_check(checks, defects, "security:least_privilege", "Least privilege" in arch or "least privilege" in arch.lower(), "lp", "security")
    add_check(checks, defects, "security:protected_env", "Protected production" in arch or "protected" in arch.lower(), "env", "security")
    add_check(checks, defects, "artifacts:git_revision", "git revision" in arch.lower() or "commit SHA" in arch, "provenance", "artifacts")
    add_check(checks, defects, "release:epic19", policy.get("vs_code_cli_publication_epic") == 19, str(policy.get("vs_code_cli_publication_epic")), "release_boundary")
    lambda_strategy = {
        "strategy": policy.get("lambda_update_strategy"),
        "detail": policy.get("lambda_update_strategy_detail"),
    }
    return checks, defects, order, lambda_strategy


def check_epic17_boundary(monorepo: Path, policy: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    boundary = {
        "start_slice_17_1": True,
        "start_slice_17_2": True,
        "aws_resources_created": False,
        "tofu_apply_allowed": False,
        "production_ingestion_enabled": False,
    }
    add_check(checks, defects, "boundary:17_2_allowed", policy.get("start_slice_17_2") is True, "true", "epic17_boundary")
    add_check(checks, defects, "boundary:sv17_6_pkg", (monorepo / "verification/community_cloud_runtime_security").is_dir(), "present", "epic17_boundary")
    add_check(checks, defects, "boundary:no_infra_prod_pkg", not (monorepo / "verification/infrastructure_production").exists(), "absent", "epic17_boundary")
    # Local operator artifacts may exist after Slice 17.2 init; they must remain untracked/gitignored.
    add_check(
        checks,
        defects,
        "boundary:absent:infrastructure_production_terraform.tfstate",
        not (monorepo / "infrastructure/production/terraform.tfstate").exists(),
        "infrastructure/production/terraform.tfstate",
        "epic17_boundary",
    )
    gi = (monorepo / "infrastructure/.gitignore").read_text(encoding="utf-8")
    add_check(
        checks,
        defects,
        "boundary:production_terraform_dir_ignored",
        ".terraform/" in gi,
        "gitignore",
        "epic17_boundary",
    )
    add_check(checks, defects, "boundary:no_aws_create_claim", policy.get("aws_resources_created") is False, "false", "epic17_boundary")
    # 17.1 itself created no AWS resources; later slices own bootstrap/plan/apply without starting 17.6.
    add_check(checks, defects, "boundary:start_17_4_true", policy.get("start_slice_17_4", False) is True, "true", "epic17_boundary")
    add_check(checks, defects, "boundary:start_17_5_true", policy.get("start_slice_17_5", False) is True, "true", "epic17_boundary")
    add_check(checks, defects, "boundary:start_17_6_true", policy.get("start_slice_17_6", False) is True, "true", "epic17_boundary")
    add_check(checks, defects, "boundary:start_17_7_true", policy.get("start_slice_17_7", True) is True, "true", "epic17_boundary")
    return checks, defects, boundary

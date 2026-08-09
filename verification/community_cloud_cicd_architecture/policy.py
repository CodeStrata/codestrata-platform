"""Policy and register presence checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_cicd_architecture.contract import (
    ARCH_DOC_RELATIVE,
    ARCH_POINTER_RELATIVE,
    CICD_REGISTER_RELATIVE,
    COMPONENT_REGISTER_RELATIVE,
    CONTRACT_RELATIVE,
    DEPLOYMENT_ORDER,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    REQUIRED_WORKFLOW_NAMES,
)
from verification.community_cloud_cicd_architecture.helpers import add_check, load_json
from verification.community_cloud_cicd_architecture.models import CheckResult, Defect


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / POLICY_RELATIVE
    add_check(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    if not path.is_file():
        return checks, defects, {}
    policy = load_json(path)
    add_check(checks, defects, "policy:schema", policy.get("schema") == POLICY_SCHEMA, str(policy.get("schema")), "policy")
    add_check(checks, defects, "policy:start_slice_17_1", policy.get("start_slice_17_1") is True, str(policy.get("start_slice_17_1")), "policy")
    add_check(
        checks,
        defects,
        "policy:start_slice_17_2_allowed",
        policy.get("start_slice_17_2") is True,
        str(policy.get("start_slice_17_2")),
        "policy",
        classification="slice_17_2_started",
    )
    for key in (
        "architecture_frozen",
        "oidc_required",
        "remote_state_required",
        "plan_apply_separated",
        "application_infra_separated",
        "production_approval_required",
    ):
        add_check(checks, defects, f"policy:{key}", policy.get(key) is True, str(policy.get(key)), "policy")
    for key in (
        "production_actions_allowed",
        "aws_resources_created",
        "tofu_apply_allowed",
        "secrets_created",
        "production_ingestion_enabled",
        "lambda_deployed",
        "insights_deployed",
        "docs_deployed",
        "validation_ci_may_deploy",
        "infrastructure_apply_on_pr",
        "long_lived_aws_access_keys_allowed",
    ):
        add_check(checks, defects, f"policy:{key}_false", policy.get(key) is False, str(policy.get(key)), "policy")
    add_check(
        checks,
        defects,
        "policy:environment_production_only",
        policy.get("environment_strategy") == "production_only",
        str(policy.get("environment_strategy")),
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:lambda_strategy",
        policy.get("lambda_update_strategy") == "ecr_immutable_image_uri_update",
        str(policy.get("lambda_update_strategy")),
        "policy",
    )
    order = policy.get("deployment_order") or []
    add_check(
        checks,
        defects,
        "policy:deployment_order",
        list(order) == list(DEPLOYMENT_ORDER),
        str(len(order)),
        "policy",
        classification="deploy_order_inversion",
    )
    mirror = monorepo / "insights/policies/community_cloud_cicd_policy.json"
    add_check(
        checks,
        defects,
        "policy:insights_mirror",
        mirror.is_file() and mirror.read_bytes() == path.read_bytes(),
        "insights mirror",
        "policy",
    )
    cpath = monorepo / CONTRACT_RELATIVE
    add_check(checks, defects, "contract:exists", cpath.is_file(), CONTRACT_RELATIVE, "policy")
    return checks, defects, policy


def check_registers(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    cicd_path = monorepo / CICD_REGISTER_RELATIVE
    comp_path = monorepo / COMPONENT_REGISTER_RELATIVE
    add_check(checks, defects, "register:cicd_exists", cicd_path.is_file(), CICD_REGISTER_RELATIVE, "inventory")
    add_check(checks, defects, "register:components_exists", comp_path.is_file(), COMPONENT_REGISTER_RELATIVE, "inventory")
    cicd: dict = {}
    components: dict = {}
    if cicd_path.is_file():
        cicd = load_json(cicd_path)
        add_check(checks, defects, "register:cicd_schema", cicd.get("schema") == "codestrata-cicd-architecture:1.0", str(cicd.get("schema")), "inventory")
        add_check(checks, defects, "register:deploy_allowed_false", cicd.get("deploy_allowed") is False, str(cicd.get("deploy_allowed")), "inventory")
        rs = cicd.get("remote_state_backend") or {}
        add_check(
            checks,
            defects,
            "register:remote_state_s3_native",
            rs.get("backend_type") == "s3"
            and rs.get("locking_method") == "s3_native_lockfile"
            and rs.get("use_lockfile") is True
            and rs.get("dynamodb_locking_required") is False,
            str(rs.get("locking_method")),
            "workflows",
        )
        names = [w.get("name") for w in cicd.get("workflows") or []]
        for name in REQUIRED_WORKFLOW_NAMES:
            add_check(checks, defects, f"register:workflow:{name}", name in names, name, "workflows")
        for w in cicd.get("workflows") or []:
            if w.get("name") == "ci":
                add_check(checks, defects, "register:ci_no_deploy", w.get("deploy_allowed") is False, str(w.get("deploy_allowed")), "workflows")
                add_check(
                    checks,
                    defects,
                    "register:ci_active",
                    w.get("current_status") == "active_validation_only",
                    str(w.get("current_status")),
                    "workflows",
                )
            elif w.get("name") == "release":
                add_check(checks, defects, "register:release_epic19", w.get("current_status") == "deferred_epic_19", str(w.get("current_status")), "release_boundary")
            else:
                add_check(
                    checks,
                    defects,
                    f"register:{w.get('name')}_inactive",
                    w.get("deploy_allowed") is False,
                    str(w.get("deploy_allowed")),
                    "workflows",
                )
    if comp_path.is_file():
        components = load_json(comp_path)
        add_check(
            checks,
            defects,
            "register:component_schema",
            components.get("schema") == "codestrata-deployment-component-register:1.0",
            str(components.get("schema")),
            "inventory",
        )
        names = {c.get("name") for c in components.get("components") or []}
        for required in (
            "Infrastructure",
            "Community Cloud API",
            "Data Lake",
            "Insights APIs",
            "Insights frontend",
            "Docs",
            "VS Code / CLI publication",
        ):
            add_check(checks, defects, f"register:component:{required}", required in names, required, "inventory")
        ownership = components.get("ownership_matrix") or {}
        add_check(checks, defects, "register:ownership_lambda_creation", bool(ownership.get("lambda_creation_config")), "present", "inventory")
        add_check(checks, defects, "register:ownership_lambda_updates", bool(ownership.get("lambda_code_package_updates")), "present", "inventory")
        for c in components.get("components") or []:
            add_check(
                checks,
                defects,
                f"register:component_no_deploy_17_1:{c.get('name')}",
                c.get("deploy_allowed_in_17_1") is False,
                str(c.get("deploy_allowed_in_17_1")),
                "epic17_boundary",
            )
            if c.get("name") == "VS Code / CLI publication":
                add_check(checks, defects, "register:vscode_epic19", c.get("epic") == 19, str(c.get("epic")), "release_boundary")
            if c.get("name") == "Insights frontend":
                add_check(checks, defects, "register:insights_no_aws_creds", c.get("frontend_aws_credentials") is False, "false", "insights")
                add_check(checks, defects, "register:insights_no_sm_read", c.get("frontend_secrets_manager_read") is False, "false", "insights")
    doc = monorepo / ARCH_DOC_RELATIVE
    ptr = monorepo / ARCH_POINTER_RELATIVE
    add_check(checks, defects, "docs:authoritative", doc.is_file(), ARCH_DOC_RELATIVE, "documentation")
    add_check(checks, defects, "docs:pointer", ptr.is_file(), ARCH_POINTER_RELATIVE, "documentation")
    if ptr.is_file():
        add_check(
            checks,
            defects,
            "docs:pointer_references_authority",
            "community-cloud-cicd-architecture.md" in ptr.read_text(encoding="utf-8"),
            "pointer",
            "documentation",
        )
    return checks, defects, cicd, components

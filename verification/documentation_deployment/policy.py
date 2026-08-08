"""Policy checks for Slice 14.12."""

from __future__ import annotations

from verification.documentation_deployment.contract import (
    ASSETS_DIR,
    DOCS_ROOT,
    POLICY_ID,
    POLICY_VERSION,
    VITEPRESS_OUT,
    WRANGLER_CONFIG,
)
from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult, Defect


def check_policy(inv: DeploymentInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = inv.policy

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "policy"))

    add(
        "policy:id_version",
        policy.get("policy_id") == POLICY_ID and policy.get("policy_version") == POLICY_VERSION,
        f"{POLICY_ID}:{POLICY_VERSION}",
    )
    add("policy:slice", policy.get("slice") == "14.12", str(policy.get("slice")))
    add(
        "policy:package_root_model_b",
        policy.get("package_root_model") == "B_docs_package_root"
        and policy.get("package_root") == DOCS_ROOT
        and policy.get("cloudflare_project_root") == DOCS_ROOT,
        "B_docs_package_root",
    )
    add(
        "policy:wrangler_config",
        policy.get("wrangler_config") == WRANGLER_CONFIG,
        str(policy.get("wrangler_config")),
    )
    add(
        "policy:vitepress_output",
        policy.get("vitepress_output_relative_to_package") == VITEPRESS_OUT,
        str(policy.get("vitepress_output_relative_to_package")),
    )
    add(
        "policy:assets_directory",
        policy.get("assets_directory") == ASSETS_DIR,
        str(policy.get("assets_directory")),
    )
    add(
        "policy:build_once",
        policy.get("build_once_required") is True
        and policy.get("build_ownership") == "A_cloudflare_build_phase",
        "A_cloudflare_build_phase",
    )
    add(
        "policy:local_wrangler",
        policy.get("local_wrangler_required") is True
        and policy.get("dynamic_wrangler_install_allowed") is False,
        "local_only",
    )
    add(
        "policy:no_production_deploy",
        policy.get("production_deploy_in_verification_allowed") is False,
        "forbidden",
    )
    add(
        "policy:no_credentials",
        policy.get("credentials_in_source_allowed") is False,
        "forbidden",
    )
    add(
        "policy:forbidden_14_13",
        policy.get("forbidden", {}).get("start_epic_15") is True,
        "prohibited",
    )
    add(
        "policy:forbidden_wrong_assets_path",
        policy.get("forbidden", {}).get("assets_directory_docs_dot_vitepress_dist") is True,
        "prohibited",
    )
    add(
        "policy:node_engines",
        policy.get("node_engines") == ">=22",
        str(policy.get("node_engines")),
    )
    add(
        "policy:expected_design_system",
        policy.get("expected_unchanged", {}).get("design_system") == "1.0",
        "1.0",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("policy", "documentation deployment policy contract mismatch"))
    return checks, defects

"""Aggregator for Slice 17.10 production recovery checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.application_update import check_application_update
from verification.community_cloud_production_recovery.baseline import check_baseline
from verification.community_cloud_production_recovery.cloudflare_docs import check_cloudflare_docs
from verification.community_cloud_production_recovery.cloudflare_insights import check_cloudflare_insights
from verification.community_cloud_production_recovery.contract import (
    CONTRACT_RELATIVE,
    INSIGHTS_POLICY_RELATIVE,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    REGISTER_RELATIVE,
    REGISTER_SCHEMA,
)
from verification.community_cloud_production_recovery.cost import check_cost
from verification.community_cloud_production_recovery.data_safety import check_data_safety
from verification.community_cloud_production_recovery.destructive_gate import check_destructive_gate
from verification.community_cloud_production_recovery.epic17_boundary import check_epic17_boundary
from verification.community_cloud_production_recovery.github_iam import check_github_iam
from verification.community_cloud_production_recovery.github_workflows import check_github_workflows
from verification.community_cloud_production_recovery.helpers import add_check, read_json
from verification.community_cloud_production_recovery.inventory import check_inventory, load_evidence
from verification.community_cloud_production_recovery.lambda_config import check_lambda_config
from verification.community_cloud_production_recovery.lambda_image import check_lambda_image
from verification.community_cloud_production_recovery.lock_recovery import check_lock_recovery
from verification.community_cloud_production_recovery.models import CheckResult, Defect
from verification.community_cloud_production_recovery.prior_slices import check_prior_slices
from verification.community_cloud_production_recovery.recovery_matrix import check_recovery_matrix
from verification.community_cloud_production_recovery.resource_classification import (
    check_resource_classification,
)
from verification.community_cloud_production_recovery.secrets_safety import check_secrets_safety
from verification.community_cloud_production_recovery.security import check_security
from verification.community_cloud_production_recovery.state_recovery import check_state_recovery
from verification.community_cloud_production_recovery.zero_drift import check_zero_drift

__all__ = [
    "check_application_update",
    "check_baseline",
    "check_cloudflare_docs",
    "check_cloudflare_insights",
    "check_cost",
    "check_data_safety",
    "check_destructive_gate",
    "check_epic17_boundary",
    "check_github_iam",
    "check_github_workflows",
    "check_inventory",
    "check_lambda_config",
    "check_lambda_image",
    "check_lock_recovery",
    "check_policy",
    "check_prior_slices",
    "check_recovery_matrix",
    "check_resource_classification",
    "check_secrets_safety",
    "check_security",
    "check_state_recovery",
    "check_zero_drift",
    "load_evidence",
]


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy: dict = {}
    register: dict = {}
    path = monorepo / POLICY_RELATIVE
    add_check(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    if path.is_file():
        policy = read_json(path)
        add_check(checks, defects, "policy:schema", policy.get("schema") == POLICY_SCHEMA, str(policy.get("schema")), "policy")
        required_true = (
            "production_recovery_ready",
            "lambda_image_rollback_ready",
            "lambda_config_rollback_ready",
            "infrastructure_rollback_ready",
            "state_recovery_ready",
            "state_lock_recovery_ready",
            "insights_rollback_ready",
            "docs_rollback_ready",
            "data_lake_destroy_forbidden",
            "remote_state_destroy_forbidden",
            "destructive_plan_gate",
            "final_zero_drift",
            "start_slice_17_10",
        )
        for key in required_true:
            add_check(checks, defects, f"policy:{key}", policy.get(key) is True, "true", "policy")
        add_check(
            checks,
            defects,
            "policy:start_17_11",
            policy.get("start_slice_17_11") is True,
            "true",
            "policy",
        )
        add_check(
            checks,
            defects,
            "policy:start_17_12_false",
            policy.get("start_slice_17_12") is True,
            "false",
            "policy",
        )
        for key in (
            "redesign_infrastructure_allowed",
            "publish_allowed",
            "tag_allowed",
            "commit_required",
        ):
            add_check(checks, defects, f"policy:{key}_false", policy.get(key) is False, "false", "policy")
        add_check(checks, defects, "policy:region", policy.get("region") == "us-west-2", str(policy.get("region")), "policy")
        add_check(
            checks,
            defects,
            "policy:environment",
            policy.get("environment") == "production",
            str(policy.get("environment")),
            "policy",
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
        register = read_json(rpath)
        add_check(
            checks,
            defects,
            "register:schema",
            register.get("schema") == REGISTER_SCHEMA,
            str(register.get("schema")),
            "policy",
        )
        add_check(
            checks,
            defects,
            "register:start_17_10",
            register.get("start_slice_17_10") is True,
            "true",
            "policy",
        )
        add_check(
            checks,
            defects,
            "register:start_17_11",
            register.get("start_slice_17_11") is True,
            "true",
            "policy",
        )
        add_check(
            checks,
            defects,
            "register:start_17_12_false",
            register.get("start_slice_17_12") is True,
            "false",
            "policy",
        )
    add_check(checks, defects, "contract:exists", (monorepo / CONTRACT_RELATIVE).is_file(), CONTRACT_RELATIVE, "policy")
    return checks, defects, policy, register

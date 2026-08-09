"""Contract for Slice 17.9."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_cloud_incremental_deployment import (
    COMMUNITY_CLOUD_INCREMENTAL_DEPLOYMENT_ID,
    VERSION,
)

SCHEMA_NAME = "community-cloud-incremental-deployment-verification"
SCHEMA_VERSION = "1.0.0"
SV179_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-9"
REPORT_JSON = "community-cloud-incremental-deployment-verification.json"
REPORT_MD = "community-cloud-incremental-deployment-verification.md"

POLICY_RELATIVE = "platform/policies/community_cloud_incremental_deployment_policy.json"
POLICY_SCHEMA = "community-cloud-incremental-deployment-policy:1.0"
REGISTER_RELATIVE = "platform/policies/community_cloud_incremental_deployment_register.json"
REGISTER_SCHEMA = "community-cloud-incremental-deployment-register:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_cloud_incremental_deployment_verification.json"
INSIGHTS_POLICY_RELATIVE = "insights/policies/community_cloud_incremental_deployment_policy.json"

EVIDENCE_DIR_RELATIVE = "infrastructure/production/.local/sv17-9"
LIFECYCLE_EVIDENCE = "lifecycle-evidence.json"
GITHUB_EVIDENCE = "github-workflow-validation.json"
OIDC_EVIDENCE = "oidc-validation.json"
OIDC_POLICY_EVIDENCE = "oidc-policy-existence.json"

PLAN_WORKFLOW = ".github/workflows/infrastructure-plan.yml"
APPLY_WORKFLOW = ".github/workflows/infrastructure-apply.yml"
PRODUCTION_ROOT = "infrastructure/production"

EXPECTED_REGION = "us-west-2"
EXPECTED_ENVIRONMENT = "production"
EXPECTED_OIDC_ROLE = "codestrata-github-actions-production"
EXPECTED_CHANGE_RESOURCE = "module.community_cloud_api.aws_cloudwatch_log_group.lambda"
EXPECTED_DEPENDENT_RESOURCE = "module.community_cloud_api.aws_iam_role_policy.lambda_logging"

OIDC_TRANSITIONAL_SUBJECTS = (
    "repo:CodeStrata/codestrata-platform:environment:production",
    "repo:CodeStrata/codestrata-infrastructure:environment:production",
)

PRIOR_REPORTS = (
    ("17.1", ".codestrata-artifacts/validation/suites/sv17-1/community-cloud-cicd-architecture-verification.json"),
    ("17.2", ".codestrata-artifacts/validation/suites/sv17-2/community-cloud-remote-state-verification.json"),
    ("17.3", ".codestrata-artifacts/validation/suites/sv17-3/community-cloud-github-oidc-verification.json"),
    ("17.4", ".codestrata-artifacts/validation/suites/sv17-4/community-cloud-production-plan-verification.json"),
    ("17.5", ".codestrata-artifacts/validation/suites/sv17-5/community-cloud-infrastructure-deployment-verification.json"),
    ("17.6", ".codestrata-artifacts/validation/suites/sv17-6/community-cloud-runtime-security-verification.json"),
    ("17.7", ".codestrata-artifacts/validation/suites/sv17-7/community-cloud-production-ingestion-verification.json"),
    ("17.8", ".codestrata-artifacts/validation/suites/sv17-8/community-production-sites-deployment-verification.json"),
)

PRIOR_POLICY_INVARIANTS = (
    (
        "platform/policies/community_cloud_cicd_policy.json",
        {"oidc_required": True, "plan_apply_separated": True},
    ),
    (
        "platform/policies/community_cloud_github_oidc_policy.json",
        {"start_slice_17_3": True},
    ),
    (
        "platform/policies/community_cloud_production_ingestion_policy.json",
        {"production_ingestion_enabled": True},
    ),
    (
        "platform/policies/community_production_sites_repository_deployment_policy.json",
        {
            "start_slice_17_8": True,
            "start_slice_17_9": True,
            "start_slice_17_10": True,
            "start_slice_17_11": True,
            "start_slice_17_12": True,
            "destructive_monorepo_cutover_allowed": False,
        },
    ),
)

SOFT_LIMITATION_CODES = frozenset(
    {
        "github_plan_apply_iam_policies_not_attached",
        "github_live_apply_path_deferred",
        "worktree_uncommitted",
        "prior_verifier_gates_stale_on_rerun",
        "dependent_iam_logging_plan_churn",
    }
)

SOFT_CHECK_IDS = frozenset(
    {
        "oidc:plan_policy_exists",
        "oidc:apply_policy_exists",
        "oidc:plan_policy_attached",
        "oidc:apply_policy_attached",
        "github:live_apply_executed",
        "regression:report_17.2",
        "regression:report_17.3",
        "regression:report_17.4",
        "regression:report_17.5",
        "regression:report_17.6",
        "regression:report_17.7",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv179Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_CLOUD_INCREMENTAL_DEPLOYMENT_ID
    package_version: str = VERSION
    start_slice_17_9: bool = True
    start_slice_17_10: bool = True
    start_slice_17_11: bool = True
    start_slice_17_12: bool = True
    start_slice_17_13: bool = False
    region: str = EXPECTED_REGION
    environment: str = EXPECTED_ENVIRONMENT


def default_contract() -> Sv179Contract:
    return Sv179Contract()

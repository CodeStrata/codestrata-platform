"""Contract for Slice 17.10."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_cloud_production_recovery import (
    COMMUNITY_CLOUD_PRODUCTION_RECOVERY_ID,
    VERSION,
)

SCHEMA_NAME = "community-cloud-production-recovery-verification"
SCHEMA_VERSION = "1.0.0"
SV1710_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-10"
REPORT_JSON = "community-cloud-production-recovery-verification.json"
REPORT_MD = "community-cloud-production-recovery-verification.md"

POLICY_RELATIVE = "platform/policies/community_cloud_production_recovery_policy.json"
POLICY_SCHEMA = "community-cloud-production-recovery-policy:1.0"
REGISTER_RELATIVE = "platform/policies/community_cloud_production_recovery_register.json"
REGISTER_SCHEMA = "community-cloud-production-recovery-register:1.0"
CLASSIFICATION_RELATIVE = "platform/policies/community_cloud_resource_recovery_classification.json"
CLASSIFICATION_SCHEMA = "community-cloud-resource-recovery-classification:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_cloud_production_recovery_verification.json"
INSIGHTS_POLICY_RELATIVE = "insights/policies/community_cloud_production_recovery_policy.json"

EVIDENCE_DIR_RELATIVE = "infrastructure/production/.local/sv17-10"
PRODUCTION_ROOT = "infrastructure/production"
FIXTURES_RELATIVE = "verification/community_cloud_production_recovery/fixtures"

PLAN_WORKFLOW = ".github/workflows/infrastructure-plan.yml"
APPLY_WORKFLOW = ".github/workflows/infrastructure-apply.yml"

EXPECTED_REGION = "us-west-2"
EXPECTED_ENVIRONMENT = "production"
EXPECTED_LAMBDA_NAME = "codestrata-community-cloud-production-api"
EXPECTED_DATA_LAKE_BUCKET = "codestrata-community-data-lake-production"
EXPECTED_OIDC_ROLE = "codestrata-github-actions-production"

EVIDENCE_FILES = (
    "baseline-summary.json",
    "lambda-baseline.json",
    "lambda-image-rollback.json",
    "lambda-config-rollback.json",
    "ecr-images.json",
    "datalake-before.json",
    "datalake-after.json",
    "state-backend.json",
    "lock-lifecycle.json",
    "destructive-gate.json",
    "github-iam.json",
    "github-workflow-validation.json",
    "insights-recovery.json",
    "docs-recovery.json",
    "secrets-safety.json",
    "recovery-matrix.json",
    "zero-drift-final.json",
    "application-update.json",
)

REQUIRED_CLASSIFICATION_COMPONENTS = (
    "Lambda",
    "API Gateway",
    "ECR",
    "CloudWatch log group",
    "IAM policies",
    "Secrets",
    "Data Lake S3",
    "remote-state S3",
    "GitHub OIDC",
)

ALLOWED_RECOVERY_MODES = frozenset(
    {
        "SAFE_IN_PLACE",
        "SAFE_RECREATE",
        "DATA_PRESERVING_ONLY",
        "NEVER_AUTOMATICALLY_DESTROY",
    }
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
    ("17.9", ".codestrata-artifacts/validation/suites/sv17-9/community-cloud-incremental-deployment-verification.json"),
)

PRIOR_POLICY_INVARIANTS = (
    (
        "platform/policies/community_cloud_incremental_deployment_policy.json",
        {
            "start_slice_17_9": True,
            "start_slice_17_10": True,
            "start_slice_17_11": True,
            "start_slice_17_12": True,
        },
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
    (
        "platform/policies/community_cloud_cicd_policy.json",
        {"oidc_required": True, "plan_apply_separated": True, "start_slice_17_10": True},
    ),
    (
        "platform/policies/community_cloud_github_oidc_policy.json",
        {"start_slice_17_3": True, "start_slice_17_10": True, "start_slice_17_11": True},
    ),
    (
        "platform/policies/community_cloud_production_ingestion_policy.json",
        {"production_ingestion_enabled": True, "start_slice_17_10": True, "start_slice_17_11": True},
    ),
)

SOFT_LIMITATION_CODES = frozenset(
    {
        "unsafe_old_lambda_image_not_activated",
        "cloudflare_redeploy_current_instead_of_old_version",
        "remote_state_recovery_read_only_simulation",
        "github_plan_apply_iam_pending_or_attached",
        "worktree_uncommitted",
        "list_object_versions_denied_for_operator",
    }
)

SOFT_CHECK_IDS = frozenset(
    {
        "inventory:evidence_partial",
        "baseline:evidence",
        "lambda_image:evidence",
        "lambda_image:rollback_executed",
        "lambda_config:evidence",
        "state_recovery:evidence",
        "state_recovery:read_only_simulation",
        "state_recovery:list_versions_denied",
        "lock_recovery:evidence",
        "cloudflare_insights:evidence",
        "cloudflare_insights:prior_version",
        "cloudflare_docs:evidence",
        "cloudflare_docs:prior_version",
        "github_iam:evidence",
        "github_iam:plan_apply_attached",
        "github_workflows:evidence",
        "application_update:evidence",
        "data_safety:evidence",
        "data_safety:list_versions",
        "secrets_safety:evidence",
        "recovery_matrix:evidence",
        "zero_drift:evidence",
        "regression:report_17.2",
        "regression:report_17.3",
        "regression:report_17.4",
        "regression:report_17.5",
        "regression:report_17.6",
        "regression:report_17.7",
        "regression:report_17.8",
        "regression:report_17.9",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1710Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_CLOUD_PRODUCTION_RECOVERY_ID
    package_version: str = VERSION
    start_slice_17_10: bool = True
    start_slice_17_11: bool = True
    start_slice_17_12: bool = True
    start_slice_17_13: bool = False
    production_recovery_ready: bool = True
    lambda_image_rollback_ready: bool = True
    lambda_config_rollback_ready: bool = True
    infrastructure_rollback_ready: bool = True
    state_recovery_ready: bool = True
    state_lock_recovery_ready: bool = True
    insights_rollback_ready: bool = True
    docs_rollback_ready: bool = True
    data_lake_destroy_forbidden: bool = True
    remote_state_destroy_forbidden: bool = True
    destructive_plan_gate: bool = True
    final_zero_drift: bool = True
    region: str = EXPECTED_REGION
    environment: str = EXPECTED_ENVIRONMENT


def default_contract() -> Sv1710Contract:
    return Sv1710Contract()

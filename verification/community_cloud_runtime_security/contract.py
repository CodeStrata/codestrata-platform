"""Contract for Slice 17.6."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_cloud_runtime_security import (
    COMMUNITY_CLOUD_RUNTIME_SECURITY_ID,
    COMMUNITY_CLOUD_RUNTIME_SECURITY_VERSION,
)

SCHEMA_NAME = "community-cloud-runtime-security-verification"
SCHEMA_VERSION = "1.0.0"
SV176_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-6"
REPORT_JSON = "community-cloud-runtime-security-verification.json"
REPORT_MD = "community-cloud-runtime-security-verification.md"

POLICY_RELATIVE = "platform/policies/community_cloud_runtime_security_policy.json"
POLICY_SCHEMA = "community-cloud-runtime-security-policy:1.0"
REGISTER_RELATIVE = "platform/policies/community_cloud_runtime_security_register.json"
REGISTER_SCHEMA = "community-cloud-runtime-security-register:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_cloud_runtime_security_verification.json"
INSIGHTS_POLICY_RELATIVE = "insights/policies/community_cloud_runtime_security_policy.json"
DEPLOYMENT_REGISTER_RELATIVE = "platform/policies/community_cloud_production_deployment_register.json"
GITHUB_APPLY_POLICY_RELATIVE = "platform/policies/codestrata_github_infrastructure_apply_policy.json"
OPERATOR_IAM_POLICY = "infrastructure/bootstrap/github-oidc/operator-iam-runtime-security-policy.json"
OPERATOR_IAM_APPLY_POLICY = "infrastructure/bootstrap/github-oidc/operator-iam-production-apply-policy.json"
INSIGHTS_AUTH_MODULE = "infrastructure/modules/community-insights-auth"
INSIGHTS_AUTH_POLICY_PY = (
    "platform/src/codestrata_platform/community_cloud_api/insights_auth/policy.py"
)
WIRING_PY = "platform/src/codestrata_platform/community_cloud_api/deployment/wiring.py"
AWS_SECRETS_PY = "platform/src/codestrata_platform/community_cloud_api/insights_auth/aws_secrets.py"
PRODUCTION_ROOT = "infrastructure/production"
RUNTIME_SECURITY_TF = "infrastructure/production/runtime-security.tf"
LOCAL_DIR_RELATIVE = "infrastructure/production/.local"
SECRETS_EVIDENCE_RELATIVE = "infrastructure/production/.local/secrets_evidence.json"
SECRETS_EVIDENCE_ALT_RELATIVE = "infrastructure/production/.local/runtime_security_secrets_evidence.json"
RUNTIME_SECURITY_EVIDENCE_RELATIVE = "infrastructure/production/.local/runtime_security_evidence.json"
RUNTIME_SECURITY_EVIDENCE_ALT_RELATIVE = "infrastructure/production/.local/runtime_security_iam_evidence.json"
DOCKERFILE_RELATIVE = "platform/deployment/community-cloud-api/Dockerfile"
SECRETS_SCRIPT = "infrastructure/scripts/configure-production-secrets.sh"
RUNTIME_IAM_SCRIPT = "infrastructure/scripts/configure-production-runtime-iam.sh"
ROTATION_DOC = "infrastructure/docs/runtime-security-secret-rotation.md"

EXPECTED_READER_POLICY = "codestrata-community-insights-production-reader"
EXPECTED_SECRETS_POLICY = "codestrata-community-insights-production-secrets"
EXPECTED_WRITER_POLICY = "codestrata-community-data-lake-production-writer"

EXPECTED_REGION = "us-west-2"
EXPECTED_ENVIRONMENT = "production"
EXPECTED_PASSWORD_SECRET_ID = "codestrata/insights/dashboard-password"
EXPECTED_SESSION_SECRET_ID = "codestrata/insights/session-secret"
EXPECTED_LAMBDA_NAME = "codestrata-community-cloud-production-api"
EXPECTED_DATA_LAKE_BUCKET = "codestrata-community-data-lake-production"
EXPECTED_WRITER_STATUS = "unattached_deferred_to_17_7"
EXPECTED_SECRET_STORAGE = "secrets_manager_only"

FORBIDDEN_RESOURCE_TYPES = frozenset(
    {
        "aws_dynamodb_table",
        "aws_athena_workgroup",
        "aws_glue_catalog_database",
        "aws_db_instance",
        "aws_elasticache_cluster",
        "aws_elasticache_replication_group",
    }
)

SECRET_VALUE_PATTERNS = (
    r"-----BEGIN",
    r"ghp_",
    r"github_pat_",
    r"AKIA[0-9A-Z]{16}",
    r"aws_secret_access_key\s*=",
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv176Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_CLOUD_RUNTIME_SECURITY_ID
    package_version: str = COMMUNITY_CLOUD_RUNTIME_SECURITY_VERSION
    start_slice_17_6: bool = True
    start_slice_17_7: bool = True
    start_slice_17_8: bool = False
    production_ingestion_enabled: bool = False
    secrets_configured: bool = True
    insights_auth_runtime_ready: bool = True
    data_lake_writer_ready: bool = True
    data_lake_reader_ready: bool = True
    provider_credentials_configured: bool = False
    writer_attached: bool = False
    region: str = EXPECTED_REGION
    environment: str = EXPECTED_ENVIRONMENT


def default_contract() -> Sv176Contract:
    return Sv176Contract()

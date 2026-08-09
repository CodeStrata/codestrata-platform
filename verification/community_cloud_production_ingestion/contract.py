"""Contract for Slice 17.7."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_cloud_production_ingestion import (
    COMMUNITY_CLOUD_PRODUCTION_INGESTION_ID,
    COMMUNITY_CLOUD_PRODUCTION_INGESTION_VERSION,
)

SCHEMA_NAME = "community-cloud-production-ingestion-verification"
SCHEMA_VERSION = "1.0.0"
SV177_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-7"
REPORT_JSON = "community-cloud-production-ingestion-verification.json"
REPORT_MD = "community-cloud-production-ingestion-verification.md"

POLICY_RELATIVE = "platform/policies/community_cloud_production_ingestion_policy.json"
POLICY_SCHEMA = "community-cloud-production-ingestion-policy:1.0"
REGISTER_RELATIVE = "platform/policies/community_cloud_production_ingestion_register.json"
REGISTER_SCHEMA = "community-cloud-production-ingestion-register:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_cloud_production_ingestion_verification.json"
INSIGHTS_POLICY_RELATIVE = "insights/policies/community_cloud_production_ingestion_policy.json"
RUNTIME_SECURITY_POLICY_RELATIVE = "platform/policies/community_cloud_runtime_security_policy.json"
PRODUCTION_ROOT = "infrastructure/production"
LOCAL_DIR_RELATIVE = "infrastructure/production/.local"
PREACTIVATION_EVIDENCE = "infrastructure/production/.local/sv17-7-preactivation.json"
ACTIVATION_EVIDENCE = "infrastructure/production/.local/sv17-7-activation.json"
STREAM_RESULTS_EVIDENCE = "infrastructure/production/.local/sv17-7-stream-results.json"
DATA_LAKE_BEFORE_EVIDENCE = "infrastructure/production/.local/sv17-7-data-lake-before.json"
DATA_LAKE_AFTER_EVIDENCE = "infrastructure/production/.local/sv17-7-data-lake-after.json"

SINKS_PY = "platform/src/codestrata_platform/community_cloud_api/data_lake/sinks.py"
WIRING_PY = "platform/src/codestrata_platform/community_cloud_api/deployment/wiring.py"
SETTINGS_PY = "platform/src/codestrata_platform/community_cloud_api/deployment/settings.py"
EVENT_IDENTITY_S3 = "platform/src/codestrata_platform/community_cloud_api/event_identity/s3_store.py"
AWS_CREDENTIALS_PY = "platform/src/codestrata_platform/community_cloud_api/authentication/aws_credentials.py"
ACTIVATE_SCRIPT = "infrastructure/scripts/activate-production-ingestion.sh"
INGESTION_CREDENTIALS_SCRIPT = "infrastructure/scripts/configure-production-ingestion-credentials.sh"
OPERATOR_IAM_POLICY = "infrastructure/bootstrap/github-oidc/operator-iam-production-ingestion-policy.json"
WRITER_POLICY_MODULE = "infrastructure/modules/community-data-lake/iam.tf"

EXPECTED_REGION = "us-west-2"
EXPECTED_ENVIRONMENT = "production"
EXPECTED_WRITER_POLICY = "codestrata-community-data-lake-production-writer"
EXPECTED_LAMBDA_NAME = "codestrata-community-cloud-production-api"
EXPECTED_DATA_LAKE_BUCKET = "codestrata-community-data-lake-production"
EXPECTED_STREAMS = (
    "telemetry",
    "assessment_metadata",
    "cli_events",
    "extension_events",
    "ai_usage",
)

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


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv177Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_CLOUD_PRODUCTION_INGESTION_ID
    package_version: str = COMMUNITY_CLOUD_PRODUCTION_INGESTION_VERSION
    start_slice_17_7: bool = True
    start_slice_17_8: bool = False
    production_ingestion_enabled: bool = True
    client_consent_still_required: bool = True
    writer_attached: bool = True
    five_streams_enabled: bool = True
    data_lake_private: bool = True
    quarantine_enabled: bool = True
    report_artifacts_in_lake: bool = False
    region: str = EXPECTED_REGION
    environment: str = EXPECTED_ENVIRONMENT


def default_contract() -> Sv177Contract:
    return Sv177Contract()

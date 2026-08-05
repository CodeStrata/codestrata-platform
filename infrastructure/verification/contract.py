"""Contract for SV.9 deployment foundation verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_ID = (
    "platform-deployment-foundation-verification"
)
PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_VERSION = "1.0.0"

MODULE_NAME = "community-cloud-api"
DATA_LAKE_MODULE_NAME = "community-data-lake"
ENVIRONMENT_NAME = "production"
DEPLOYMENT_MODE = "production_foundation"
AUTHENTICATION_MODE = "enabled_verifier_unavailable"
RATE_LIMIT_MODE = "api_gateway_plus_process_local"
REQUIRED_OPENTOFU = ">= 1.6.0"
AWS_PROVIDER_CONSTRAINT = ">= 5.0.0, < 6.0.0"
LAMBDA_ARCHITECTURE_DEFAULT = "arm64"
API_GATEWAY_PROTOCOL = "HTTP"
PACKAGING_STRATEGY = "lambda_container_ecr"

REQUIRED_MODULE_FILES: tuple[str, ...] = (
    "main.tf",
    "variables.tf",
    "outputs.tf",
    "versions.tf",
    "api_gateway.tf",
    "lambda.tf",
    "iam.tf",
    "ecr.tf",
    "logging.tf",
    "throttling.tf",
    "configuration.tf",
    "validation.tf",
)

REQUIRED_DATA_LAKE_MODULE_FILES: tuple[str, ...] = (
    "main.tf",
    "variables.tf",
    "outputs.tf",
    "versions.tf",
    "locals.tf",
    "storage.tf",
    "encryption.tf",
    "lifecycle.tf",
    "iam.tf",
    "validation.tf",
    "README.md",
)

REQUIRED_VARIABLES: tuple[str, ...] = (
    "project_name",
    "environment_name",
    "aws_region",
    "lambda_function_name",
    "lambda_memory_size",
    "lambda_timeout_seconds",
    "lambda_architecture",
    "lambda_image_uri",
    "api_name",
    "api_stage_name",
    "log_retention_days",
    "deployment_mode",
    "authentication_mode",
    "rate_limit_mode",
    "enable_ingestion",
    "tags",
)

REQUIRED_OUTPUTS: tuple[str, ...] = (
    "api_endpoint",
    "health_endpoint",
    "lambda_function_name",
    "lambda_function_arn",
    "api_gateway_id",
    "log_group_name",
    "ecr_repository_url",
    "deployment_mode",
)

FORBIDDEN_RESOURCE_TYPES: tuple[str, ...] = (
    "aws_s3_bucket",
    "aws_dynamodb_table",
    "aws_sqs_queue",
    "aws_sns_topic",
    "aws_kinesis_stream",
    "aws_secretsmanager_secret",
    "aws_ssm_parameter",
    "aws_cognito_user_pool",
    "aws_wafv2_web_acl",
    "aws_apigatewayv2_authorizer",
    "aws_api_gateway_rest_api",
)

FORBIDDEN_IAM_ACTIONS: tuple[str, ...] = (
    "s3:",
    "dynamodb:",
    "sqs:",
    "sns:",
    "kinesis:",
    "secretsmanager:",
    "ssm:",
    "bedrock:",
    "iam:Create",
    "iam:Delete",
    "iam:Put",
    "iam:Attach",
    "apigateway:POST",
    "apigateway:DELETE",
)

INGESTION_PATHS: tuple[str, ...] = (
    "/api/v1/telemetry",
    "/api/v1/assessment-metadata",
    "/api/v1/cli-events",
    "/api/v1/extension-events",
    "/api/v1/ai-usage",
)

SAFETY_PATTERNS: tuple[tuple[str, str], ...] = (
    ("aws_access_key", r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])"),
    ("aws_secret_assign", r"(?i)aws_secret_access_key\s*=\s*['\"][^'\"]{8,}"),
    ("bearer", r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    ("cscc_credential", r"cscc_v1_[A-Za-z0-9_]+"),
    ("private_key", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ("home_path", r"(?<![\w.-])/Users/[\w.-]+"),
    ("file_uri", r"file" + r"://[/\w]"),
)

FORBIDDEN_REPORT_FRAGMENTS: tuple[str, ...] = (
    "AKIA",
    "-----BEGIN",
    "/Users/",
    "/home/",
    "cscc_v1_",
)


def infra_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repo_root() -> Path:
    return infra_root().parent


@dataclass(frozen=True, slots=True)
class DeploymentVerificationContract:
    verification_id: str = PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_ID
    schema_version: str = PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_VERSION
    notes: tuple[str, ...] = (
        "SV.9 verifies the Slice 7.14 production deployment foundation.",
        "Does not run tofu apply, terraform apply, Docker build/push, or AWS deploy.",
        "OpenTofu CLI validation is reported honestly when tofu is unavailable.",
        "Does not start SV.10 or the 30-repository run.",
        "Community Data Lake foundation (Slice 8.1) exists but is unwired: "
        "no ingestion, no analytics layer.",
    )


def default_contract() -> DeploymentVerificationContract:
    return DeploymentVerificationContract()

"""Module contract and configuration static checks."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[1]
MODULE = INFRA / "modules" / "community-cloud-api"
PROD = INFRA / "production"


def _read(*parts: str) -> str:
    return (INFRA.joinpath(*parts)).read_text(encoding="utf-8")


def test_production_uses_module_and_label() -> None:
    main = _read("production", "main.tf")
    assert 'module "community_cloud_api"' in main
    assert 'environment_name         = "production"' in main
    assert 'deployment_mode          = "production_foundation"' in main
    assert "enable_ingestion         = false" in main
    assert 'authentication_mode      = "enabled_verifier_unavailable"' in main


def test_outputs_are_safe() -> None:
    outputs = _read("modules", "community-cloud-api", "outputs.tf")
    for forbidden in (
        "secret",
        "password",
        "token",
        "credential",
        "fingerprint",
        "authorization",
    ):
        assert forbidden not in outputs.lower() or "description" in outputs.lower()
    # Explicit safe outputs present
    for name in (
        "api_endpoint",
        "health_endpoint",
        "lambda_function_name",
        "lambda_function_arn",
        "api_gateway_id",
        "log_group_name",
        "ecr_repository_url",
        "deployment_mode",
    ):
        assert f'output "{name}"' in outputs

    prod_outputs = _read("production", "outputs.tf")
    for name in (
        "api_base_url",
        "health_url",
        "lambda_function_name",
        "lambda_function_arn",
        "api_gateway_id",
        "ecr_repository_url",
        "cloudwatch_log_group",
        "deployment_mode",
    ):
        assert f'output "{name}"' in prod_outputs


def test_single_lambda_proxy_for_all_routes() -> None:
    api = _read("modules", "community-cloud-api", "api_gateway.tf")
    assert 'protocol_type = "HTTP"' in api
    assert 'integration_type       = "AWS_PROXY"' in api
    assert 'route_key = "ANY /{proxy+}"' in api
    assert "aws_lambda_function" in _read("modules", "community-cloud-api", "lambda.tf")
    # No per-endpoint Lambdas
    lambda_tf = _read("modules", "community-cloud-api", "lambda.tf")
    assert lambda_tf.count('resource "aws_lambda_function"') == 1
    assert "authorizer" not in api.lower()
    assert "cors_configuration" not in api
    assert "domain_name" not in api.lower()


def test_no_data_lake_or_queue_resources() -> None:
    blob = "\n".join(
        path.read_text(encoding="utf-8") for path in MODULE.glob("*.tf")
    )
    for forbidden in (
        'resource "aws_s3_bucket"',
        'resource "aws_dynamodb_table"',
        'resource "aws_sqs_queue"',
        'resource "aws_kinesis_stream"',
        'resource "aws_secretsmanager_secret"',
        "aws_waf",
        "aws_cognito",
    ):
        assert forbidden not in blob, forbidden


def test_lambda_bounds_and_image() -> None:
    variables = _read("modules", "community-cloud-api", "variables.tf")
    assert "lambda_memory_size" in variables
    assert "lambda_timeout_seconds" in variables
    assert "arm64" in variables
    lambda_tf = _read("modules", "community-cloud-api", "lambda.tf")
    assert 'package_type  = "Image"' in lambda_tf
    assert "vpc_config" not in lambda_tf


def test_ecr_private_immutable_scanning() -> None:
    ecr = _read("modules", "community-cloud-api", "ecr.tf")
    assert 'image_tag_mutability = "IMMUTABLE"' in ecr
    assert "scan_on_push = true" in ecr
    assert 'encryption_type = "AES256"' in ecr
    assert "aws_ecr_lifecycle_policy" in ecr
    assert "public" not in ecr.lower() or "no public" in ecr.lower()


def test_logging_retention_explicit() -> None:
    logging = _read("modules", "community-cloud-api", "logging.tf")
    assert "retention_in_days = var.log_retention_days" in logging
    variables = _read("modules", "community-cloud-api", "variables.tf")
    assert "default     = 30" in variables


def test_configuration_fail_closed() -> None:
    config = _read("modules", "community-cloud-api", "configuration.tf")
    assert "CODESTRATA_DEPLOYMENT_MODE" in config
    assert "CODESTRATA_AUTHENTICATION_ENABLED" in config
    assert "CODESTRATA_INGESTION_ENABLED" in config
    assert "No secrets" in config


def test_iam_least_privilege() -> None:
    iam = _read("modules", "community-cloud-api", "iam.tf")
    assert "logs:CreateLogStream" in iam
    assert "logs:PutLogEvents" in iam
    assert "ecr:BatchGetImage" in iam
    assert "s3:" not in iam.lower()
    assert "dynamodb:" not in iam.lower()
    assert "sqs:" not in iam.lower()
    assert "secretsmanager:" not in iam.lower()
    # Documented AWS exception for GetAuthorizationToken only.
    assert 'ecr:GetAuthorizationToken' in iam
    assert iam.count('resources = ["*"]') == 1
    assert 'Action = "*"' not in iam
    assert 'actions = ["*"]' not in iam


def test_tfvars_example_placeholders_only() -> None:
    example = _read("production", "terraform.tfvars.example")
    assert "REPLACE_ME" in example
    assert "cscc_v1_" not in example
    assert "AKIA" not in example

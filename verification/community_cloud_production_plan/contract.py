"""Contract for Slice 17.4."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_cloud_production_plan import (
    COMMUNITY_CLOUD_PRODUCTION_PLAN_ID,
    COMMUNITY_CLOUD_PRODUCTION_PLAN_VERSION,
)

SCHEMA_NAME = "community-cloud-production-plan-verification"
SCHEMA_VERSION = "1.0.0"
SV174_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-4"
REPORT_JSON = "community-cloud-production-plan-verification.json"
REPORT_MD = "community-cloud-production-plan-verification.md"

POLICY_RELATIVE = "platform/policies/community_cloud_production_plan_policy.json"
POLICY_SCHEMA = "community-cloud-production-plan-policy:1.0"
REGISTER_RELATIVE = "platform/policies/community_cloud_production_plan_register.json"
REGISTER_SCHEMA = "community-cloud-production-plan-register:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_cloud_production_plan_verification.json"
APPLY_REGISTER_RELATIVE = "platform/policies/community_cloud_apply_permission_register.json"
GITHUB_PLAN_POLICY_RELATIVE = "platform/policies/codestrata_github_infrastructure_plan_policy.json"
INSIGHTS_POLICY_RELATIVE = "insights/policies/community_cloud_production_plan_policy.json"
DOCS_RELATIVE = "infrastructure/docs/production-plan.md"
WORKFLOW_RELATIVE = ".github/workflows/infrastructure-plan.yml"
PLAN_SCRIPT_RELATIVE = "infrastructure/scripts/plan-production.sh"
PRODUCTION_ROOT = "infrastructure/production"
SANITIZED_INVENTORY_RELATIVE = "infrastructure/production/.local/sv17-4-sanitized-inventory.json"
PLAN_JSON_RELATIVE = "infrastructure/production/.local/sv17-4.tfplan.json"
PLAN_JSON_B_RELATIVE = "infrastructure/production/.local/sv17-4-b.tfplan.json"

EXPECTED_REGION = "us-west-2"
EXPECTED_ENVIRONMENT = "production"
EXPECTED_ADD = 21
EXPECTED_CHANGE = 0
EXPECTED_DESTROY = 0
EXPECTED_REPLACE = 0
EXPECTED_DATA_LAKE_BUCKET = "codestrata-community-data-lake-production"
EXPECTED_LAMBDA_NAME = "codestrata-community-cloud-production-api"
EXPECTED_ECR_NAME = "codestrata/community-cloud-api"
EXPECTED_PLAN_EXECUTOR = "local_codestrata_infra"

ALLOWED_RESOURCE_CLASSES = frozenset({"REQUIRED_V0_2_0", "SUPPORTING_REQUIRED"})
FORBIDDEN_RESOURCE_TYPES = frozenset(
    {
        "aws_dynamodb_table",
        "aws_athena_workgroup",
        "aws_glue_catalog_database",
        "aws_db_instance",
        "aws_elasticache_cluster",
        "aws_instance",
        "aws_ecs_service",
        "aws_eks_cluster",
        "aws_nat_gateway",
        "aws_opensearch_domain",
        "aws_redshift_cluster",
        "aws_lb",
        "aws_secretsmanager_secret",
        "aws_secretsmanager_secret_version",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv174Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_CLOUD_PRODUCTION_PLAN_ID
    package_version: str = COMMUNITY_CLOUD_PRODUCTION_PLAN_VERSION
    start_slice_17_4: bool = True
    start_slice_17_5: bool = True
    start_slice_17_6: bool = True
    start_slice_17_7: bool = True
    start_slice_17_8: bool = False
    plan_only: bool = True
    product_apply: bool = False
    production_ingestion_enabled: bool = False
    region: str = EXPECTED_REGION
    environment: str = EXPECTED_ENVIRONMENT


def default_contract() -> Sv174Contract:
    return Sv174Contract()

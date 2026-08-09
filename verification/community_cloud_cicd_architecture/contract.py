"""Contract for Slice 17.1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_cloud_cicd_architecture import (
    COMMUNITY_CLOUD_CICD_ARCHITECTURE_ID,
    COMMUNITY_CLOUD_CICD_ARCHITECTURE_VERSION,
)

SCHEMA_NAME = "community-cloud-cicd-architecture-verification"
SCHEMA_VERSION = "1.0.0"
SV171_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-1"
REPORT_JSON = "community-cloud-cicd-architecture-verification.json"
REPORT_MD = "community-cloud-cicd-architecture-verification.md"

POLICY_RELATIVE = "platform/policies/community_cloud_cicd_policy.json"
POLICY_SCHEMA = "community-cloud-cicd-policy:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_cloud_cicd_architecture_verification.json"
CICD_REGISTER_RELATIVE = "platform/policies/codestrata_cicd_architecture.json"
COMPONENT_REGISTER_RELATIVE = "platform/policies/codestrata_deployment_component_register.json"
ARCH_DOC_RELATIVE = "platform/docs/deployment/community-cloud-cicd-architecture.md"
ARCH_POINTER_RELATIVE = "infrastructure/docs/cicd-architecture.md"

REQUIRED_WORKFLOW_NAMES = (
    "ci",
    "infrastructure-plan",
    "infrastructure-apply",
    "platform-deploy",
    "insights-deploy",
    "docs-deploy",
    "release",
)

DEPLOYMENT_ORDER = (
    "bootstrap_remote_state",
    "establish_github_oidc",
    "production_tofu_plan",
    "infrastructure_apply",
    "secrets_manager_configuration",
    "runtime_iam",
    "platform_backend_deployment",
    "enable_ingestion",
    "insights_frontend_deployment",
    "docs_deployment",
    "production_smoke",
    "repo_suite_validation",
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv171Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_CLOUD_CICD_ARCHITECTURE_ID
    package_version: str = COMMUNITY_CLOUD_CICD_ARCHITECTURE_VERSION
    start_slice_17_1: bool = True
    start_slice_17_2: bool = True
    production_actions_allowed: bool = False
    aws_resources_created: bool = False
    tofu_apply_allowed: bool = False
    production_ingestion_enabled: bool = False
    long_lived_aws_keys_allowed: bool = False
    validation_ci_may_deploy: bool = False


def default_contract() -> Sv171Contract:
    return Sv171Contract()

"""Contract constants for Slice 12.5 Infrastructure repository structure."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.infrastructure_repository_contract import (
    INFRASTRUCTURE_REPOSITORY_CONTRACT_ID,
    INFRASTRUCTURE_REPOSITORY_CONTRACT_VERSION,
)

SCHEMA_NAME = "infrastructure-repository-contract-verification"
SCHEMA_VERSION = "1.0.0"

SV125_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv12-5"
REPORT_JSON = "infrastructure-repository-contract-verification.json"
REPORT_MD = "infrastructure-repository-contract-verification.md"

REPOSITORY_NAME = "codestrata-infrastructure"
REPOSITORY_VISIBILITY = "private"

SOURCE_AUTHORITY_DECISION = (
    "pre_cutover_main_monorepo_authoritative;"
    "post_cutover_infrastructure_repository_authoritative;"
    "dual_authoring_forbidden;"
    "export_one_way"
)
DESTINATION_LAYOUT_DECISION = "approach_a_remove_infrastructure_prefix"

POLICY_ID = "community-infrastructure-repository-policy"
POLICY_VERSION = "1.0"
POLICY_URN = f"{POLICY_ID}:{POLICY_VERSION}"

MANIFEST_SCHEMA_NAME = "infrastructure-repository-export-manifest"
MANIFEST_SCHEMA_VERSION = "1.0.0"

ASSESSMENT_SCHEMA_VERSION = "1.2"

VALIDATION_ROOTS = (
    "modules/community-cloud-api",
    "modules/community-data-lake",
    "production",
)

REQUIRED_ALLOWLIST = (
    "infrastructure/modules/",
    "infrastructure/production/",
    "infrastructure/tests/",
    "infrastructure/verification/",
    "infrastructure/docs/",
    "infrastructure/policies/",
    "infrastructure/scripts/",
    "infrastructure/README.md",
    "infrastructure/__init__.py",
    "infrastructure/.gitignore",
)

OPTIONAL_ALLOWLIST = (
    "infrastructure/production/backend.tf.example",
    "infrastructure/production/terraform.tfvars.example",
    "infrastructure/**/.terraform.lock.hcl",
)

PROHIBITED_CATEGORIES = (
    "git_metadata",
    "terraform_state",
    "terraform_plans",
    "provider_plugin_cache",
    "credentials_and_env",
    "generated_caches",
    "generated_reports",
    "engine_runtime",
    "platform_runtime",
    "vscode_extension",
    "cursor_extension",
    "community_release_artifacts",
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv125Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = INFRASTRUCTURE_REPOSITORY_CONTRACT_ID
    package_version: str = INFRASTRUCTURE_REPOSITORY_CONTRACT_VERSION
    start_slice_12_6: bool = False
    no_export: bool = True
    no_destination_repo: bool = True
    no_git_init: bool = True
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    no_aws: bool = True
    no_opentofu_plan_apply: bool = True
    no_infrastructure_behavior_change: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION
    repository_name: str = REPOSITORY_NAME
    repository_visibility: str = REPOSITORY_VISIBILITY
    source_authority_decision: str = SOURCE_AUTHORITY_DECISION
    destination_layout_decision: str = DESTINATION_LAYOUT_DECISION
    policy_urn: str = POLICY_URN


def default_contract() -> Sv125Contract:
    return Sv125Contract()

"""Contract for Slice 16.6 storage & generated cleanup."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.repository_storage_generated_cleanup import (
    REPOSITORY_STORAGE_GENERATED_CLEANUP_ID,
    REPOSITORY_STORAGE_GENERATED_CLEANUP_VERSION,
)

SCHEMA_NAME = "repository-storage-generated-cleanup-verification"
SCHEMA_VERSION = "1.0.0"
SV166_OUTPUT_RELATIVE = "reports/verification/sv16-6"
REPORT_JSON = "repository-storage-generated-cleanup-verification.json"
REPORT_MD = "repository-storage-generated-cleanup-verification.md"

POLICY_ID = "repository-storage-generated-cleanup-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/repository_storage_generated_cleanup_policy.json"
POLICY_SCHEMA = "repository-storage-generated-cleanup-policy:1.0"
REGISTER_RELATIVE = "platform/policies/repository_generated_artifact_register.json"

CLASSIFICATIONS: tuple[str, ...] = (
    "SOURCE_REQUIRED",
    "TRACKED_GENERATED_REQUIRED",
    "GENERATED_RECREATABLE",
    "LOCAL_RUNTIME_STATE",
    "TEST_FIXTURE_REQUIRED",
    "VERIFICATION_OUTPUT",
    "BUILD_OUTPUT",
    "CACHE",
    "EXPORT_STAGING",
    "SCRATCH",
    "HISTORICAL_ARCHIVE",
    "DELETE",
    "GITIGNORE_REQUIRED",
    "OWNER_REVIEW_REQUIRED",
)

REMOVED_LOCAL_PATHS: tuple[str, ...] = (
    ".codestrata",
    "engine/.codestrata",
    ".codestrata-test-knowledge",
    "engine/.codestrata-test-knowledge",
    ".export-staging",
    "docs/.vitepress/dist",
    "insights/dist",
    "vscode-plugin/out",
    "vscode-plugin/codestrata-vscode-0.2.0.vsix",
    "dist",
    "engine/dist",
    "platform/dist",
    ".mypy_cache",
    "engine/.mypy_cache",
    ".pytest_cache",
    "infrastructure/production/.terraform",
    "infrastructure/modules/community-cloud-api/.terraform",
    "infrastructure/modules/community-data-lake/.terraform",
)

PROTECTED_PATHS: tuple[str, ...] = (
    "design-system/assets/brand",
    "docs/package-lock.json",
    "vscode-plugin/package-lock.json",
    "test-fixtures",
    "infrastructure/production/.terraform.lock.hcl",
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv166Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = REPOSITORY_STORAGE_GENERATED_CLEANUP_ID
    package_version: str = REPOSITORY_STORAGE_GENERATED_CLEANUP_VERSION
    start_slice_16_7: bool = True
    start_slice_16_8: bool = True
    start_slice_16_9: bool = True
    start_slice_16_10: bool = True
    start_epic_17: bool = False
    no_dependency_changes: bool = True
    no_repository_relocation: bool = True
    no_runtime_semantic_change: bool = True
    production_ingestion_enabled: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv166Contract:
    return Sv166Contract()

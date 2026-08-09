"""Contract for Slice 16.5 dependency & build cleanup."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.repository_dependency_build_cleanup import (
    REPOSITORY_DEPENDENCY_BUILD_CLEANUP_ID,
    REPOSITORY_DEPENDENCY_BUILD_CLEANUP_VERSION,
)

SCHEMA_NAME = "repository-dependency-build-cleanup-verification"
SCHEMA_VERSION = "1.0.0"
SV165_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv16-5"
REPORT_JSON = "repository-dependency-build-cleanup-verification.json"
REPORT_MD = "repository-dependency-build-cleanup-verification.md"

POLICY_ID = "repository-dependency-build-cleanup-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/repository_dependency_build_cleanup_policy.json"
POLICY_SCHEMA = "repository-dependency-build-cleanup-policy:1.0"
DEPENDENCY_REGISTER_RELATIVE = "platform/policies/repository_dependency_register.json"
BUILD_REGISTER_RELATIVE = "platform/policies/repository_build_authority_register.json"

CLASSIFICATIONS: tuple[str, ...] = (
    "RUNTIME_REQUIRED",
    "BUILD_REQUIRED",
    "TEST_REQUIRED",
    "VERIFICATION_REQUIRED",
    "EXPORT_REQUIRED",
    "RELEASE_REQUIRED",
    "OPTIONAL_FEATURE",
    "TRANSITIVE_ONLY",
    "UNUSED_REMOVE",
    "DUPLICATE_DECLARATION",
    "OVERBROAD_DEPENDENCY",
    "SECURITY_REVIEW_REQUIRED",
    "OWNER_REVIEW_REQUIRED",
    "UPGRADE_DEFERRED",
)

ENGINE_VERSION = "0.2.0"
VSCODE_VERSION = "0.2.0"


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv165Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = REPOSITORY_DEPENDENCY_BUILD_CLEANUP_ID
    package_version: str = REPOSITORY_DEPENDENCY_BUILD_CLEANUP_VERSION
    start_slice_16_6: bool = True
    start_slice_16_7: bool = True
    start_slice_16_8: bool = True
    start_slice_16_9: bool = True
    start_slice_16_10: bool = True
    start_epic_17: bool = True
    start_slice_17_2: bool = True
    no_storage_cleanup: bool = True
    no_repository_split: bool = True
    no_forced_framework_modernization: bool = True
    no_product_version_changes: bool = True
    production_ingestion_enabled: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv165Contract:
    return Sv165Contract()

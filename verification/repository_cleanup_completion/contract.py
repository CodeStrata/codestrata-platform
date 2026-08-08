"""Contract for Slice 16.10 Epic 16 completion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.repository_cleanup_completion import (
    REPOSITORY_CLEANUP_COMPLETION_ID,
    REPOSITORY_CLEANUP_COMPLETION_VERSION,
)

SCHEMA_NAME = "repository-cleanup-completion-verification"
SCHEMA_VERSION = "1.0.0"
SV1610_OUTPUT_RELATIVE = "reports/verification/sv16-10"
REPORT_JSON = "repository-cleanup-completion-verification.json"
REPORT_MD = "repository-cleanup-completion-verification.md"

POLICY_RELATIVE = "platform/policies/repository_cleanup_completion_policy.json"
POLICY_SCHEMA = "repository-cleanup-completion-policy:1.0"
CONTRACT_RELATIVE = "platform/contracts/repository_cleanup_completion_verification.json"
OWNER_REGISTER_RELATIVE = "platform/policies/repository_owner_review_register.json"

SLICE_MATRIX = (
    ("16.1", "Repository Inventory & Classification", "repository_inventory", "repository-cleanup-policy:1.0", "repository-inventory-verification"),
    ("16.2", "Community Documentation Cleanup", "repository_documentation", "repository-documentation-policy:1.0", "repository-documentation-verification"),
    ("16.3", "Repository Code Cleanup", "repository_code_cleanup", "repository-code-cleanup-policy:1.0", "repository-code-cleanup-verification"),
    ("16.4", "Asset & Design Cleanup", "repository_asset_design_cleanup", "repository-asset-design-cleanup-policy:1.0", "repository-asset-design-cleanup-verification"),
    ("16.5", "Dependency & Build Cleanup", "repository_dependency_build_cleanup", "repository-dependency-build-cleanup-policy:1.0", "repository-dependency-build-cleanup-verification"),
    ("16.6", "Storage & Generated Artifact Cleanup", "repository_storage_generated_cleanup", "repository-storage-generated-cleanup-policy:1.0", "repository-storage-generated-cleanup-verification"),
    ("16.7", "Repository Boundary & Residency Cleanup", "repository_boundary_residency", "repository-boundary-residency-policy:1.0", "repository-boundary-residency-verification"),
    ("16.8", "Repository Consistency Validation", "repository_consistency", "repository-consistency-policy:1.0", "repository-consistency-verification"),
    ("16.9", "Community Package & Release Artifact Validation", "repository_package_release_validation", "repository-package-release-validation-policy:1.0", "repository-package-release-validation-verification"),
    ("16.10", "Repository Cleanup Completion Verification", "repository_cleanup_completion", "repository-cleanup-completion-policy:1.0", "repository-cleanup-completion-verification"),
)

REQUIRED_TOP_LEVEL = (
    "engine", "platform", "infrastructure", "vscode-plugin", "insights",
    "docs", "design-system", "verification", "tests", "scripts",
    "governance", "validation", "examples",
)

VERSION_ANCHORS = {"engine_cli": "0.2.0", "vscode": "0.2.0", "assessment": "1.2", "design_system": "1.0"}


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1610Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = REPOSITORY_CLEANUP_COMPLETION_ID
    package_version: str = REPOSITORY_CLEANUP_COMPLETION_VERSION
    start_slice_16_10: bool = True
    start_epic_17: bool = False
    epic_complete: bool = True
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    no_remote_creation: bool = True
    no_cutover: bool = True
    production_ingestion_enabled: bool = False


def default_contract() -> Sv1610Contract:
    return Sv1610Contract()

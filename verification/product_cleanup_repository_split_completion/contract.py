"""Contract for Epic 12 completion verification (Slice 12.10)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.product_cleanup_repository_split_completion import (
    PRODUCT_CLEANUP_REPOSITORY_SPLIT_COMPLETION_ID,
    PRODUCT_CLEANUP_REPOSITORY_SPLIT_COMPLETION_VERSION,
)

SCHEMA_NAME = "product-cleanup-repository-split-completion-verification"
SCHEMA_VERSION = "1.0.0"

EPIC = 12
RELEASE = "0.2.0"
TOTAL_SLICES = 10
COMPLETED_SLICES = 10

SV1210_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv12-10"
REPORT_JSON = "product-cleanup-repository-split-completion-verification.json"
REPORT_MD = "product-cleanup-repository-split-completion-verification.md"

ASSESSMENT_SCHEMA_VERSION = "1.2"
INTENDED_ENGINE_VERSION = "0.2.0"
INTENDED_VSCODE_VERSION = "0.2.0"

ACTIVE_EDITOR_EXTENSIONS = ("vscode",)
ACTIVE_CLIENTS = ("codestrata_cli", "vscode_extension")
RETIRED_CLIENTS = ("cursor_extension",)
EXPORT_TARGETS = ("community", "infrastructure", "insights")
TARGET_VISIBILITY = {
    "community": "public_product_export",
    "infrastructure": "private",
    "insights": "private_internal_application",
}

POLICY_REGISTRY = {
    "community-retired-client-policy": "1.0",
    "community-infrastructure-repository-policy": "1.0",
}

MANIFEST_REGISTRY = {
    "codestrata.community_release": "2",
    "infrastructure-repository-export-manifest": "1.0.0",
}

EPIC12_VERIFICATION_SCHEMAS = {
    "12.1": "cursor-extension-removal-verification:1.0.0",
    "12.2": "cursor-release-surface-removal-verification:1.0.0",
    "12.3": "cursor-documentation-removal-verification:1.0.0",
    "12.4": "community-client-boundary-cleanup-verification:1.0.0",
    "12.5": "infrastructure-repository-contract-verification:1.0.0",
    "12.6": "infrastructure-repository-exporter-verification:1.0.0",
    "12.7": "infrastructure-repository-export-verification:1.0.0",
    "12.8": "repository-export-target-verification:1.0.0",
    "12.9": "ci-release-boundary-verification:1.0.0",
    "12.10": "product-cleanup-repository-split-completion-verification:1.0.0",
}

PRODUCT_SCHEMA_REGISTRY = {
    "assessment": "1.2",
    "engine_product_version": "0.2.0",
    "vscode_extension_version": "0.2.0",
    "infrastructure_versioning": "independent",
    "platform_versioning": "independent",
}

ALLOWED_LIMITATIONS = frozenset(
    {
        "worktree_uncommitted",
        "no_remote_infrastructure_repository",
        "no_remote_github_actions_execution",
        "no_live_marketplace_publication",
        "no_production_plan_apply",
        "provider_plugin_download_or_cache_during_init",
        "historical_cursor_records_retained",
        "source_cutover_deferred",
        "owner_migration_deferred",
        "no_full_vscode_extension_host_ui_automation",
    }
)

FORBIDDEN_REPORT_FRAGMENTS = (
    "/Users/",
    "/home/",
    "file://",
    "-----BEGIN",
    "AKIA",
    "AWS_SECRET",
    "amazonaws.com",
)

RELEASE_POSTURE = {
    "epic_12_complete_for_v0_2_0": True,
    "no_commit_in_this_slice": True,
    "no_tag": True,
    "no_publish": True,
    "no_deploy": True,
    "no_aws_service_call": True,
    "no_plan_apply_destroy": True,
    "no_real_community_or_infrastructure_repository_created": True,
    "worktree_may_contain_intended_uncommitted_epic_12_changes": True,
    "tagging_gated_by_end_to_end_smoke": True,
    "owner_cutover_future_work": True,
    "epic_13_future_work": True,
}


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1210Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = PRODUCT_CLEANUP_REPOSITORY_SPLIT_COMPLETION_ID
    package_version: str = PRODUCT_CLEANUP_REPOSITORY_SPLIT_COMPLETION_VERSION
    epic: int = EPIC
    release: str = RELEASE
    completed_slices: int = COMPLETED_SLICES
    total_slices: int = TOTAL_SLICES
    start_epic_13: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    no_plan: bool = True
    no_apply: bool = True
    no_destroy: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION


def default_contract() -> Sv1210Contract:
    return Sv1210Contract()

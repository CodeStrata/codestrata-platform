"""Contract for Slice 16.4 asset & design cleanup."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.repository_asset_design_cleanup import (
    REPOSITORY_ASSET_DESIGN_CLEANUP_ID,
    REPOSITORY_ASSET_DESIGN_CLEANUP_VERSION,
)

SCHEMA_NAME = "repository-asset-design-cleanup-verification"
SCHEMA_VERSION = "1.0.0"
SV164_OUTPUT_RELATIVE = "reports/verification/sv16-4"
REPORT_JSON = "repository-asset-design-cleanup-verification.json"
REPORT_MD = "repository-asset-design-cleanup-verification.md"

POLICY_ID = "repository-asset-design-cleanup-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/repository_asset_design_cleanup_policy.json"
POLICY_SCHEMA = "repository-asset-design-cleanup-policy:1.0"
MANIFEST_RELATIVE = "design-system/assets/asset-authority-manifest.json"
TOKEN_AUTHORITY = "design-system/tokens/tokens.css"
BRAND_MASTER = "design-system/assets/brand"
HISTORICAL_ARCHIVE = "governance/assets"
BRAND_GENERATOR = "scripts/generate_brand_assets.py"

CLASSIFICATIONS: tuple[str, ...] = (
    "AUTHORITATIVE_MASTER",
    "AUTHORIZED_DERIVATIVE",
    "GENERATED_COPY",
    "ACTIVE_SURFACE_ASSET",
    "ACTIVE_CONSUMER_TOKEN_BRIDGE",
    "HISTORICAL_ARCHIVE",
    "TEST_FIXTURE",
    "VISUAL_BASELINE",
    "STALE_DUPLICATE",
    "ORPHAN",
    "DELETE_CANDIDATE",
    "OWNER_REVIEW_REQUIRED",
    "DEFER_TO_STORAGE_CLEANUP",
    "DEFER_TO_REPOSITORY_SPLIT",
)

REMOVED_PATHS: tuple[str, ...] = (
    "insights/public/brand/codestrata-lockup-horizontal-on-dark.svg",
)

LEGACY_AMBER = "#d98a3d"

ACTIVE_TOKEN_SURFACES: tuple[str, ...] = (
    "design-system/tokens/tokens.css",
    "docs/public/design-tokens/tokens.css",
    "docs/.vitepress/theme/tokens.css",
    "platform/api/openapi/swagger/design-tokens/tokens.css",
    "insights/public/design-tokens/tokens.css",
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv164Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = REPOSITORY_ASSET_DESIGN_CLEANUP_ID
    package_version: str = REPOSITORY_ASSET_DESIGN_CLEANUP_VERSION
    no_redesign: bool = True
    start_slice_16_5: bool = True
    start_slice_16_6: bool = True
    start_slice_16_7: bool = True
    start_slice_16_8: bool = True
    start_slice_16_9: bool = True
    start_slice_16_10: bool = True
    start_epic_17: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv164Contract:
    return Sv164Contract()

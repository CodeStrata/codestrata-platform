"""Contract for Slice 14.6 Marketplace visual assets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.marketplace_visual_assets import (
    MARKETPLACE_VISUAL_ID,
    MARKETPLACE_VISUAL_VERSION,
)

SCHEMA_NAME = "marketplace-visual-assets-verification"
SCHEMA_VERSION = "1.0.0"
SV146_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv14-6"
REPORT_JSON = "marketplace-visual-assets-verification.json"
REPORT_MD = "marketplace-visual-assets-verification.md"

POLICY_ID = "codestrata-marketplace-visual-assets-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "vscode-plugin/policies/marketplace_visual_assets_policy.json"
MAPPING_RELATIVE = "vscode-plugin/policies/design_system_marketplace_mapping.json"
MANIFEST_RELATIVE = "vscode-plugin/policies/marketplace_visual_manifest.json"
PACKAGE_JSON = "vscode-plugin/package.json"
README_RELATIVE = "vscode-plugin/README.md"
ACTIVITY_SVG = "vscode-plugin/media/codestrata-activity.svg"
ICON_RELATIVE = "vscode-plugin/media/codestrata-icon.png"
VISUAL_DOC = "vscode-plugin/docs/marketplace-visual-assets.md"

GALLERY_ORDER = (
    "media/screenshot-assessment.png",
    "media/screenshot-report.png",
    "media/screenshot-progress.png",
    "media/screenshot-initialization.png",
    "media/screenshot-ai-assessment.png",
)

PUBLIC_SCREENSHOT_BASE = "https://docs.codestrata.ai/media/vscode-marketplace/"

RETIRED_ASSETS = (
    "media/screenshot-findings.png",
    "media/screenshot-findings-light.png",
    "media/screenshot-activity.png",
    "media/screenshot-recommendations.png",
)

SCREENSHOT_WIDTH = 1280
SCREENSHOT_HEIGHT = 720
ICON_SIZE = 128
BANNER_COLOR = "#f4f6f3"
BANNER_THEME = "light"

FORBIDDEN_14_8_PATHS = (
    "verification/chart_standardization",
    "verification/score_risk_visualization",
    "design-system/applications/charts",
)

LEGACY_AMBER = ("#d98a3d", "#D97706", "#F59E0B", "#FBBF24")
LEGACY_DARK = ("#0f1216", "#0b0d10")

UNSAFE_TEXT_FRAGMENTS = (
    "/Users/",
    "/home/",
    "C:\\",
    "cursor",
    "AKIA",
    "sk-",
    "ghp_",
    "Data Lake",
    "portfolio dashboard",
    "engineering intelligence report",
)

STALE_UX_FRAGMENTS = (
    "Report ready",
    "Open HTML Report now",
    "Get started with Cursor",
)

ALLOWED_LIMITATIONS = frozenset(
    {
        "extension_host_screenshot_automation_may_be_unavailable",
        "pixel_perfect_screenshot_determinism_depends_on_rendering_host",
        "universal_logo_authority_deferred_to_14_10",
        "marketplace_not_remotely_previewed_or_published",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv146Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = MARKETPLACE_VISUAL_ID
    package_version: str = MARKETPLACE_VISUAL_VERSION
    start_slice_14_7: bool = False
    no_runtime_behavior_change: bool = True
    no_universal_logo_authority_change: bool = True
    no_commit: bool = True


def default_contract() -> Sv146Contract:
    return Sv146Contract()

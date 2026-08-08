"""Contract for Slice 13.12 Marketplace branding verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_marketplace_branding import (
    VSCODE_MARKETPLACE_BRANDING_ID,
    VSCODE_MARKETPLACE_BRANDING_VERSION,
)

SCHEMA_NAME = "vscode-marketplace-branding-verification"
SCHEMA_VERSION = "1.0.0"
SV1312_OUTPUT_RELATIVE = "reports/verification/sv13-12"
REPORT_JSON = "vscode-marketplace-branding-verification.json"
REPORT_MD = "vscode-marketplace-branding-verification.md"

BRANDING_POLICY_ID = "community-vscode-marketplace-branding-policy"
BRANDING_POLICY_VERSION = "1.0"
INTENDED_VSCODE_VERSION = "0.2.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"
BRANDING_PACKAGE = "vscode-plugin/src/marketplaceBranding"
PLUGIN_ROOT = "vscode-plugin"

DISPLAY_NAME = "CodeStrata – Engineering Intelligence"
PUBLISHER = "codestrata"
PACKAGE_NAME = "codestrata-vscode"
GALLERY_COLOR = "#f4f6f3"
GALLERY_THEME = "light"
ICON_RELATIVE = "media/codestrata-icon.png"
ICON_WIDTH = 128
ICON_HEIGHT = 128

GALLERY_ORDER = (
    "media/screenshot-assessment.png",
    "media/screenshot-report.png",
    "media/screenshot-progress.png",
    "media/screenshot-initialization.png",
    "media/screenshot-ai-assessment.png",
)

VSCODE_CATEGORIES = frozenset(
    {
        "Azure",
        "Data Science",
        "Debuggers",
        "Extension Packs",
        "Education",
        "Formatters",
        "Keymaps",
        "Language Packs",
        "Linters",
        "Machine Learning",
        "Notebooks",
        "Programming Languages",
        "SCM Providers",
        "Snippets",
        "Testing",
        "Themes",
        "Visualization",
        "Other",
    }
)

FORBIDDEN_CLAIM_FRAGMENTS = (
    "fully autonomous modernization",
    "100% anonymous telemetry",
    "all code stays local",
    "all source always stays local",
    "zero data leaves",
    "no network ever",
    "automatic cli installation",
    "automatically installs",
    "supports cursor",
    "production cloud insights",
    "production telemetry",
    "guaranteed security",
    "aimf",
    "ai modernization factory",
    "codestrata cursor",
    "codestrata ai scanner",
)

PRIVATE_URL_FRAGMENTS = (
    "codestrata-platform",
    "codestrata-infrastructure",
    "platform.codestrata.ai",
    "infrastructure/",
)

ALLOWED_LIMITATIONS = frozenset(
    {
        "marketplace_listing_copy_complete_via_13_13",
        "clean_install_validation_complete_via_13_14",
        "cross_product_design_system_deferred_to_epic_14",
        "no_remote_marketplace_preview",
        "no_live_marketplace_upload",
        "screenshots_from_synthetic_fixtures",
        "no_full_extension_host_visual_automation",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1312Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_MARKETPLACE_BRANDING_ID
    package_version: str = VSCODE_MARKETPLACE_BRANDING_VERSION
    start_epic_14: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv1312Contract:
    return Sv1312Contract()

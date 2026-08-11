"""Contract for Slice 13.13 Marketplace documentation verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_marketplace_docs import (
    VSCODE_MARKETPLACE_DOCS_ID,
    VSCODE_MARKETPLACE_DOCS_VERSION,
)

SCHEMA_NAME = "vscode-marketplace-documentation-verification"
SCHEMA_VERSION = "1.0.0"
SV1313_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv13-13"
REPORT_JSON = "vscode-marketplace-documentation-verification.json"
REPORT_MD = "vscode-marketplace-documentation-verification.md"

DOCS_POLICY_ID = "community-vscode-marketplace-documentation-policy"
DOCS_POLICY_VERSION = "1.0"
BRANDING_POLICY_VERSION = "1.0"
INTENDED_VSCODE_VERSION = "0.2.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"
DOCS_PACKAGE = "vscode-plugin/src/marketplaceDocs"
README_RELATIVE = "vscode-plugin/README.md"
MARKETPLACE_MD_RELATIVE = "vscode-plugin/MARKETPLACE.md"

DISPLAY_NAME = "CodeStrata – Engineering Assessment"
TAGLINE = "Engineering decisions grounded in code."

REQUIRED_HEADINGS = (
    "What CodeStrata Does",
    "What You Get",
    "Requirements",
    "Quick Start",
    "CLI Installation",
    "Repository Initialization",
    "Running an Assessment",
    "Assessment with AI",
    "Progress",
    "Reports",
    "Failure and Recovery",
    "CLI Compatibility",
    "Privacy and Source Locality",
    "Telemetry",
    "Security",
    "Known Limitations",
    "Support",
)

GALLERY_ORDER = (
    "media/screenshot-assessment.png",
    "media/screenshot-report.png",
    "media/screenshot-progress.png",
    "media/screenshot-initialization.png",
    "media/screenshot-ai-assessment.png",
)

FORBIDDEN_CLAIM_FRAGMENTS = (
    "supports cursor",
    "vscode and cursor",
    "automatically installs",
    "automatic cli installation",
    "all data always stays local",
    "nothing ever leaves your machine",
    "no network is ever used",
    "your data never leaves your machine",
    "we collect anonymous usage analytics",
    "production telemetry is operational",
    "cloud dashboard",
    "data lake sync",
    "synced insights",
    "team dashboards",
    "autonomous remediation",
    "available now on marketplace",
    "published on the marketplace",
)

FORBIDDEN_INTERNAL_FRAGMENTS = (
    "slice 13.",
    "epic 13",
    "epic 14",
    "verification/",
    "sv13-",
    "policy_id",
    "not started",
    "\ntodo",
    "\ntbd",
    "todo:",
    "tbd:",
)

PRIVATE_URL_FRAGMENTS = (
    "codestrata-platform",
    "codestrata-infrastructure",
    "platform.codestrata.ai",
)

AI_QUALIFICATION = (
    "The VS Code extension does not directly send repository source to AI providers."
)

ALLOWED_LIMITATIONS = frozenset(
    {
        "clean_install_validation_complete_via_13_14",
        "cross_product_docs_redesign_deferred_to_epic_14",
        "no_remote_marketplace_preview",
        "no_live_marketplace_upload",
        "links_not_remotely_fetched",
        "no_full_marketplace_renderer_automation",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1313Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_MARKETPLACE_DOCS_ID
    package_version: str = VSCODE_MARKETPLACE_DOCS_VERSION
    start_epic_14: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv1313Contract:
    return Sv1313Contract()

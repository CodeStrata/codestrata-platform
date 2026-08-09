"""Contract for Slice 14.5."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_visual_experience import VSCODE_VISUAL_ID, VSCODE_VISUAL_VERSION

SCHEMA_NAME = "vscode-visual-experience-verification"
SCHEMA_VERSION = "1.0.0"
SV145_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv14-5"
REPORT_JSON = "vscode-visual-experience-verification.json"
REPORT_MD = "vscode-visual-experience-verification.md"

POLICY_ID = "codestrata-vscode-visual-experience-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "vscode-plugin/policies/vscode_visual_experience_policy.json"
MAPPING_RELATIVE = "vscode-plugin/policies/design_system_vscode_mapping.json"
PACKAGE_JSON = "vscode-plugin/package.json"
ACTIVITY_SVG = "vscode-plugin/media/codestrata-activity.svg"
PRESENTATION_COPY = "vscode-plugin/src/ui/presentationCopy.ts"
VISUAL_DOC = "vscode-plugin/docs/visual-experience.md"

FORBIDDEN_14_8_PATHS = (
    "verification/chart_standardization",
    "verification/score_risk_visualization",
    "design-system/applications/charts",
)

FORBIDDEN_CSS_IMPORTS = (
    "design-system/tokens/tokens.css",
    "tokens/tokens.css",
)

LEGACY_RUNTIME_HEX = ("#D97706", "#F59E0B", "#FBBF24", "#d98a3d")

ALLOWED_LIMITATIONS = frozenset(
    {
        "extension_host_screenshot_automation_may_be_unavailable",
        "native_surfaces_cannot_match_website_pixel_for_pixel",
        "marketplace_assets_aligned_via_14_6",
        "marketplace_assets_deferred_to_14_6",
        "final_icon_logo_authority_deferred_to_14_10",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv145Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_VISUAL_ID
    package_version: str = VSCODE_VISUAL_VERSION
    start_slice_14_6: bool = False
    no_runtime_behavior_change: bool = True
    no_marketplace_asset_change: bool = False  # owned by Slice 14.6
    no_commit: bool = True


def default_contract() -> Sv145Contract:
    return Sv145Contract()

"""Contract for Slice 14.1 visual design system verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.visual_design_system import (
    VISUAL_DESIGN_SYSTEM_ID,
    VISUAL_DESIGN_SYSTEM_VERSION,
)

SCHEMA_NAME = "codestrata-visual-design-system-verification"
SCHEMA_VERSION = "1.0.0"
SV141_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv14-1"
REPORT_JSON = "codestrata-visual-design-system-verification.json"
REPORT_MD = "codestrata-visual-design-system-verification.md"

DESIGN_SYSTEM_ROOT = "design-system"
DESIGN_SYSTEM_POLICY_ID = "codestrata-design-system-policy"
DESIGN_SYSTEM_POLICY_VERSION = "1.0"
VISUAL_LANGUAGE_POLICY_ID = "codestrata-visual-language-policy"
VISUAL_LANGUAGE_POLICY_VERSION = "1.0"

REQUIRED_DIRS = (
    "tokens",
    "colors",
    "typography",
    "spacing",
    "elevation",
    "icons",
    "components",
    "layouts",
    "themes",
    "accessibility",
    "responsive",
    "documentation",
    "surfaces",
    "policies",
    "source",
)

REQUIRED_COMPONENT_IDS = (
    "button",
    "card",
    "table",
    "panel",
    "sidebar",
    "navigation",
    "tabs",
    "progress",
    "chart",
    "badge",
    "alert",
    "score_card",
    "evidence_card",
    "recommendation_card",
)

REQUIRED_SURFACES = (
    "documentation",
    "assessment_report",
    "engineering_intelligence_report",
    "vscode_extension",
    "marketplace_assets",
)

# Slice 14.2 markers that must remain absent.
FORBIDDEN_14_2_PATHS = (
    "verification/docs_site_redesign",
    "verification/visual_docs_application",
    "design-system/applications/docs",
    "design-system/applications/assessment_report",
)

ALLOWED_LIMITATIONS = frozenset(
    {
        "definition_only_no_product_application",
        "historical_amber_tokens_superseded_by_live_website",
        "slice_14_2_not_started",
        "worktree_uncommitted",
        "no_live_axe_ci_gate",
        "marketplace_assets_not_regenerated",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv141Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VISUAL_DESIGN_SYSTEM_ID
    package_version: str = VISUAL_DESIGN_SYSTEM_VERSION
    start_slice_14_2: bool = False
    product_redesign_allowed: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv141Contract:
    return Sv141Contract()

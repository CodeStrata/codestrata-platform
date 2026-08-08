"""Contract for Slice 14.7."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.cross_surface_presentation import CROSS_SURFACE_ID, CROSS_SURFACE_VERSION

SCHEMA_NAME = "cross-surface-presentation-verification"
SCHEMA_VERSION = "1.0.0"
SV147_OUTPUT_RELATIVE = "reports/verification/sv14-7"
REPORT_JSON = "cross-surface-presentation-verification.json"
REPORT_MD = "cross-surface-presentation-verification.md"

POLICY_ID = "codestrata-cross-surface-presentation-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "design-system/policies/cross_surface_presentation_policy.json"
PRESENTATION_CONTRACT = "design-system/contracts/presentation.json"
COMPONENT_CONTRACT = "design-system/contracts/components.json"
CONSUMER_MAPPINGS = "design-system/contracts/consumer-mappings.json"
TOKEN_CATALOG = "design-system/tokens/catalog.json"
TOKEN_CSS = "design-system/tokens/tokens.css"

FORBIDDEN_EPIC_15_PATHS = (
    "verification/epic15_start",
    "verification/epic_15",
    "tests/verification/epic15_start",
    "reports/verification/sv15-1",
)

REQUIRED_TYPOGRAPHY_ROLES = (
    "display",
    "h1",
    "h2",
    "h3",
    "h4",
    "body",
    "body-small",
    "meta",
    "label",
    "metric",
    "caption",
    "code",
)

REQUIRED_COMPONENTS = (
    "product_bar",
    "page_shell",
    "section_header",
    "card",
    "summary_card",
    "metric_card",
    "finding_card",
    "evidence_block",
    "recommendation_card",
    "status_badge",
    "risk_badge",
    "callout",
    "data_table",
    "code_block",
    "empty_state",
    "navigation_item",
    "divider",
    "primary_action",
    "secondary_action",
)

LEGACY_ACTIVE_HEX = (
    "#d98a3d",
    "#D97706",
    "#F59E0B",
    "#FBBF24",
    "#0f1216",
    "#0b0d10",
    "#F4F1EA",
)

ALLOWED_LIMITATIONS = frozenset(
    {
        "chart_standardization_complete_via_14_8_foundation",
        "chart_standardization_deferred_to_14_8",
        "navigation_ia_complete_via_14_9",
        "navigation_ia_deferred_to_14_9",
        "universal_asset_authority_complete_via_14_10",
        "technology_specific_implementations_remain",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv147Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = CROSS_SURFACE_ID
    package_version: str = CROSS_SURFACE_VERSION
    start_epic_15: bool = False
    no_runtime_behavior_change: bool = True
    no_commit: bool = True


def default_contract() -> Sv147Contract:
    return Sv147Contract()

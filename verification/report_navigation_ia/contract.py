"""Contract for Slice 14.9."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.report_navigation_ia import REPORT_IA_ID, REPORT_IA_VERSION

SCHEMA_NAME = "report-navigation-information-architecture-verification"
SCHEMA_VERSION = "1.0.0"
SV149_OUTPUT_RELATIVE = "reports/verification/sv14-9"
REPORT_JSON = "report-navigation-information-architecture-verification.json"
REPORT_MD = "report-navigation-information-architecture-verification.md"

POLICY_ID = "codestrata-report-information-architecture-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "design-system/policies/report_information_architecture_policy.json"
IA_CONTRACT = "design-system/contracts/report-information-architecture.json"
VIZ_CONTRACT = "design-system/contracts/visualization.json"
PRESENTATION_CONTRACT = "design-system/contracts/presentation.json"
PRESENTATION_POLICY = "design-system/policies/cross_surface_presentation_policy.json"

ASSESSMENT_RENDERER = "engine/src/codestrata/reporting/html_v2/renderer.py"
ASSESSMENT_BUILDER = "engine/src/codestrata/reporting/html_v2/builder.py"
ASSESSMENT_STYLES = "engine/src/codestrata/reporting/html_v2/styles.py"
ASSESSMENT_HEADS = "engine/src/codestrata/reporting/html_v2/assessment_heads.py"
EIR_RENDERER = (
    "platform/src/codestrata_platform/intelligence_reporting/"
    "presentation/static_html/renderer.py"
)
EIR_SECTIONS = (
    "platform/src/codestrata_platform/intelligence_reporting/"
    "presentation/static_html/sections.py"
)
EIR_STYLES = (
    "platform/src/codestrata_platform/intelligence_reporting/"
    "presentation/static_html/styles.py"
)
EIR_DEMO_CATALOG = "platform/demo/catalog.json"

# Assessment section order authority (Epic 3 / SV.5). 14.9 must not reorder it.
ASSESSMENT_SECTION_ORDER: tuple[str, ...] = (
    "leadership-verdict",
    "executive-summary",
    "engineering-intelligence-summary",
    "key-takeaways",
    "priority-actions",
    "engineering-risks",
    "assessment-results",
    "phased-modernization-plan",
    "technical-appendix",
)

ASSESSMENT_STABLE_ANCHORS: tuple[str, ...] = (
    "cover",
    "contents",
    "main-content",
    *ASSESSMENT_SECTION_ORDER,
    "technology-inventory",
    "architecture-intelligence",
    "technical-debt-intelligence",
    "dependency-intelligence",
    "security-intelligence",
    "cloud-readiness",
    "ai-readiness",
    "modernization-assessment",
)

# Pre-Epic-3 Domain Intelligence deep links preserved as anchor-only aliases.
ASSESSMENT_LEGACY_ALIASES: tuple[str, ...] = (
    "architecture-assessment",
    "technical-debt-assessment",
    "dependency-assessment",
    "security-assessment",
    "cloud-assessment",
    "ai-readiness-assessment",
)

EIR_SECTION_ORDER: tuple[str, ...] = (
    "scope",
    "orientation",
    "summary",
    "technology",
    "capability",
    "heads",
    "patterns",
    "observations",
    "confidence",
    "limitations",
    "drilldowns",
    "methodology",
    "metadata",
)

# Slice 14.14 must not have started.
FORBIDDEN_15_7_PATHS = (
    "reports/verification/sv15-7",
)

ALLOWED_LIMITATIONS = frozenset(
    {
        "no_browser_screenshot_validation",
        "active_section_scroll_tracking_intentionally_absent",
        "legacy_pack_anchor_aliases_retained",
        "report_products_have_different_section_inventories",
        "assessment_head_pack_heading_depth_remains_legacy",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv149Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = REPORT_IA_ID
    package_version: str = REPORT_IA_VERSION
    start_slice_15_7: bool = False
    no_schema_change: bool = True
    no_section_reorder: bool = True
    no_commit: bool = True


def default_contract() -> Sv149Contract:
    return Sv149Contract()

"""Contract for Slice 14.3 assessment HTML report redesign verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.assessment_report_redesign import (
    ASSESSMENT_REPORT_REDESIGN_ID,
    ASSESSMENT_REPORT_REDESIGN_VERSION,
)

SCHEMA_NAME = "assessment-html-report-redesign-verification"
SCHEMA_VERSION = "1.0.0"
SV143_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv14-3"
REPORT_JSON = "assessment-html-report-redesign-verification.json"
REPORT_MD = "assessment-html-report-redesign-verification.md"

POLICY_ID = "codestrata-assessment-report-design-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "engine/policies/assessment_report_design_policy.json"

DESIGN_SYSTEM_TOKENS = "design-system/tokens/tokens.css"
DESIGN_SYSTEM_CATALOG = "design-system/tokens/catalog.json"
ENGINE_TOKENS = "engine/src/codestrata/design_system/tokens.py"
ENGINE_STYLES = "engine/src/codestrata/reporting/html_v2/styles.py"
ENGINE_RENDERER = "engine/src/codestrata/reporting/html_v2/renderer.py"
ASSESSMENT_SCHEMA_CONSTANTS = "engine/src/codestrata/reporting/contract/constants.py"
ASSESSMENT_SCHEMA_JSON = (
    "engine/src/codestrata/resources/schemas/assessment/"
    "codestrata.io/v1.2/AssessmentReport.json"
)

EIR_STATIC_HTML_ROOT = (
    "platform/src/codestrata_platform/intelligence_reporting/"
    "presentation/static_html"
)

FORBIDDEN_14_4_PATHS = (
    "verification/engineering_intelligence_report_redesign",
    "design-system/applications/engineering_intelligence_report",
    "platform/policies/engineering_intelligence_report_design_policy.json",
)

STABLE_SECTION_IDS = (
    "cover",
    "contents",
    "leadership-verdict",
    "executive-summary",
    "engineering-intelligence-summary",
    "key-takeaways",
    "priority-actions",
    "engineering-risks",
    "assessment-results",
    "technical-appendix",
)

LEGACY_AMBER_HEX = (
    "#f7f5f2",
    "#b06a24",
    "#d98a3d",
    "#4fb3a5",
)

ALLOWED_LIMITATIONS = frozenset(
    {
        "browser_screenshot_validation_may_be_unavailable",
        "dark_theme_refinement_may_continue_in_14_11",
        "chart_system_provisional_until_14_8",
        "cross_report_information_hierarchy_deferred_to_14_9",
        "print_pagination_not_publication_quality",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv143Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = ASSESSMENT_REPORT_REDESIGN_ID
    package_version: str = ASSESSMENT_REPORT_REDESIGN_VERSION
    start_slice_14_4: bool = False
    no_eir_redesign: bool = True
    no_assessment_schema_bump: bool = True
    no_scoring_changes: bool = True
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv143Contract:
    return Sv143Contract()

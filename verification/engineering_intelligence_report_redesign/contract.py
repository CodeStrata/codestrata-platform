"""Contract for Slice 14.4 EIR redesign verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.engineering_intelligence_report_redesign import (
    EIR_REPORT_REDESIGN_ID,
    EIR_REPORT_REDESIGN_VERSION,
)

SCHEMA_NAME = "engineering-intelligence-report-redesign-verification"
SCHEMA_VERSION = "1.0.0"
SV144_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv14-4"
REPORT_JSON = "engineering-intelligence-report-redesign-verification.json"
REPORT_MD = "engineering-intelligence-report-redesign-verification.md"

POLICY_ID = "codestrata-engineering-intelligence-report-design-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/engineering_intelligence_report_design_policy.json"

DESIGN_SYSTEM_TOKENS = "design-system/tokens/tokens.css"
DESIGN_SYSTEM_CATALOG = "design-system/tokens/catalog.json"
EIR_STYLES = (
    "platform/src/codestrata_platform/intelligence_reporting/"
    "presentation/static_html/styles.py"
)
EIR_RENDERER = (
    "platform/src/codestrata_platform/intelligence_reporting/"
    "presentation/static_html/renderer.py"
)
EIR_POLICY = (
    "platform/src/codestrata_platform/intelligence_reporting/"
    "application/website_export/policy.py"
)
EIR_DOMAIN_REPORT = (
    "platform/src/codestrata_platform/intelligence_reporting/domain/report.py"
)
ASSESSMENT_CONSTANTS = "engine/src/codestrata/reporting/contract/constants.py"
ASSESSMENT_STYLES = "engine/src/codestrata/reporting/html_v2/styles.py"
ASSESSMENT_REPORT_POLICY = "engine/policies/assessment_report_design_policy.json"

STABLE_SECTION_IDS = (
    "main",
    "section-scope",
    "section-orientation",
    "section-summary",
    "section-technology",
    "section-capability",
    "section-heads",
    "section-patterns",
    "section-observations",
    "section-confidence",
    "section-limitations",
    "section-drilldowns",
    "section-methodology",
    "section-metadata",
)

LEGACY_EIR_HEX = ("#0f4c5c", "#8a5a00", "#f7f8fa")

FORBIDDEN_14_5_PATHS = (
    "verification/vscode_ui_redesign",
    "verification/marketplace_asset_redesign",
    "design-system/applications/vscode",
)

ALLOWED_LIMITATIONS = frozenset(
    {
        "browser_screenshot_validation_may_be_unavailable",
        "chart_system_provisional_until_14_8",
        "cross_report_information_hierarchy_deferred_to_14_9",
        "print_pagination_not_publication_quality",
        "commercial_prototype_sections_retained_not_promoted",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv144Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = EIR_REPORT_REDESIGN_ID
    package_version: str = EIR_REPORT_REDESIGN_VERSION
    start_slice_14_5: bool = False
    no_assessment_regression: bool = True
    no_eir_domain_schema_bump: bool = True
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv144Contract:
    return Sv144Contract()

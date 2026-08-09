"""Contract for Slice 14.14 Epic 14 completion verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.unified_product_experience_completion import (
    UNIFIED_PRODUCT_EXPERIENCE_COMPLETION_ID,
    UNIFIED_PRODUCT_EXPERIENCE_COMPLETION_VERSION,
)

SCHEMA_NAME = "unified-product-experience-completion-verification"
SCHEMA_VERSION = "1.0.0"
SV1414_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv14-14"
REPORT_JSON = "unified-product-experience-completion-verification.json"
REPORT_MD = "unified-product-experience-completion-verification.md"

POLICY_ID = "codestrata-unified-product-experience-completion-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = (
    "design-system/policies/unified_product_experience_completion_policy.json"
)

EPIC = "14"
EPIC_TITLE = "Unified CodeStrata Community Experience"
TOTAL_SLICES = 14
DESIGN_SYSTEM_VERSION = "1.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"
EXTENSION_VERSION = "0.2.0"
MARKETPLACE_VERSION = "0.2.0"
EIR_DOMAIN_SCHEMA_VERSION = "1.0"
EIR_EXPORT_SCHEMA_VERSION = "1.0"

# slice, module, schema, title, policy_id
PRIOR_SLICE_RUNNERS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "14.1",
        "verification.visual_design_system.runner",
        "codestrata-visual-design-system-verification",
        "Establish CodeStrata Visual Design System",
        "codestrata-visual-design-system:1.0",
    ),
    (
        "14.2",
        "verification.community_documentation_redesign.runner",
        "community-documentation-redesign-verification",
        "Redesign Community Documentation",
        "community-documentation-redesign-policy:1.0",
    ),
    (
        "14.3",
        "verification.assessment_report_redesign.runner",
        "assessment-html-report-redesign-verification",
        "Redesign Assessment HTML Report",
        "codestrata-assessment-report-design-policy:1.0",
    ),
    (
        "14.4",
        "verification.engineering_intelligence_report_redesign.runner",
        "engineering-intelligence-report-redesign-verification",
        "Redesign Engineering Intelligence Report",
        "codestrata-engineering-intelligence-report-design-policy:1.0",
    ),
    (
        "14.5",
        "verification.vscode_visual_experience.runner",
        "vscode-visual-experience-verification",
        "Align VS Code Visual Experience",
        "codestrata-vscode-visual-experience-policy:1.0",
    ),
    (
        "14.6",
        "verification.marketplace_visual_assets.runner",
        "marketplace-visual-assets-verification",
        "Align Marketplace Visual Assets",
        "codestrata-marketplace-visual-assets-policy:1.0",
    ),
    (
        "14.7",
        "verification.cross_surface_presentation.runner",
        "cross-surface-presentation-verification",
        "Cross-Surface Presentation Standard",
        "codestrata-cross-surface-presentation-policy:1.0",
    ),
    (
        "14.8",
        "verification.visualization_system.runner",
        "visualization-system-verification",
        "Visualization Semantics",
        "codestrata-visualization-policy:1.0",
    ),
    (
        "14.9",
        "verification.report_navigation_ia.runner",
        "report-navigation-information-architecture-verification",
        "Report Information Architecture",
        "codestrata-report-information-architecture-policy:1.0",
    ),
    (
        "14.10",
        "verification.brand_assets.runner",
        "brand-assets-verification",
        "Brand Asset Authority",
        "codestrata-brand-asset-policy:1.0",
    ),
    (
        "14.11",
        "verification.responsive_accessibility.runner",
        "responsive-accessibility-verification",
        "Accessibility and Responsive Experience",
        "codestrata-accessibility-responsive-policy:1.0",
    ),
    (
        "14.12",
        "verification.documentation_deployment.runner",
        "documentation-deployment-verification",
        "Documentation Build and Cloudflare Deployment",
        "codestrata-documentation-deployment-policy:1.0",
    ),
    (
        "14.13",
        "verification.cross_surface_visual_consistency.runner",
        "cross-surface-visual-consistency-verification",
        "Cross-Surface Visual Consistency",
        "codestrata-cross-surface-consistency-policy:1.0",
    ),
)

EPIC14_POLICIES: tuple[tuple[str, str, str], ...] = (
    (
        "codestrata-design-system-policy",
        "1.0",
        "design-system/policies/design_system_policy.json",
    ),
    (
        "codestrata-visual-language-policy",
        "1.0",
        "design-system/policies/visual_language_policy.json",
    ),
    (
        "community-documentation-redesign-policy",
        "1.0",
        "docs/policies/community_documentation_redesign_policy.json",
    ),
    (
        "codestrata-assessment-report-design-policy",
        "1.0",
        "engine/policies/assessment_report_design_policy.json",
    ),
    (
        "codestrata-engineering-intelligence-report-design-policy",
        "1.0",
        "platform/policies/engineering_intelligence_report_design_policy.json",
    ),
    (
        "codestrata-vscode-visual-experience-policy",
        "1.0",
        "vscode-plugin/policies/vscode_visual_experience_policy.json",
    ),
    (
        "codestrata-marketplace-visual-assets-policy",
        "1.0",
        "vscode-plugin/policies/marketplace_visual_assets_policy.json",
    ),
    (
        "codestrata-cross-surface-presentation-policy",
        "1.0",
        "design-system/policies/cross_surface_presentation_policy.json",
    ),
    (
        "codestrata-visualization-policy",
        "1.0",
        "design-system/policies/visualization_policy.json",
    ),
    (
        "codestrata-report-information-architecture-policy",
        "1.0",
        "design-system/policies/report_information_architecture_policy.json",
    ),
    (
        "codestrata-brand-asset-policy",
        "1.0",
        "design-system/policies/brand_asset_policy.json",
    ),
    (
        "codestrata-accessibility-responsive-policy",
        "1.0",
        "design-system/policies/accessibility_responsive_policy.json",
    ),
    (
        "codestrata-documentation-deployment-policy",
        "1.0",
        "docs/policies/documentation_deployment_policy.json",
    ),
    (
        "codestrata-cross-surface-consistency-policy",
        "1.0",
        "design-system/policies/cross_surface_consistency_policy.json",
    ),
    (
        "codestrata-unified-product-experience-completion-policy",
        "1.0",
        POLICY_RELATIVE,
    ),
)

FORBIDDEN_15_7_PATHS: tuple[str, ...] = (
    ".codestrata-artifacts/validation/suites/sv17-1",
)

ALLOWED_LIMITATIONS: frozenset[str] = frozenset(
    {
        "no_production_cloudflare_upload",
        "marketplace_unpublished",
        "no_formal_wcag_certification",
        "manual_screen_reader_session_not_performed",
        "one_chromium_one_os",
        "historical_amber_archive_retained",
        "docs_dependency_advisories_deferred",
        "legacy_epic_11_13_historic_verification_drift_retained",
        "worktree_uncommitted",
        "v0_2_0_not_tagged_or_released",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1414Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = UNIFIED_PRODUCT_EXPERIENCE_COMPLETION_ID
    package_version: str = UNIFIED_PRODUCT_EXPERIENCE_COMPLETION_VERSION
    start_slice_15_7: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    marketplace_published: bool = False
    docs_production_deployed: bool = False
    production_deploy_complete: bool = False
    release_tag_created: bool = False


def default_contract() -> Sv1414Contract:
    return Sv1414Contract()

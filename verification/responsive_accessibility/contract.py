"""Contract for Slice 14.11 (responsive + accessible experience acceptance)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "responsive-accessibility-verification"
SCHEMA_VERSION = "1.0.0"
SV1411_OUTPUT_RELATIVE = "reports/verification/sv14-11"
REPORT_JSON = "responsive-accessibility-verification.json"
REPORT_MD = "responsive-accessibility-verification.md"
BROWSER_ARTIFACT = "browser-validation.json"

POLICY_ID = "codestrata-accessibility-responsive-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "design-system/policies/accessibility_responsive_policy.json"

ACCESSIBILITY_CONTRACT = "design-system/contracts/accessibility.json"
RESPONSIVE_CONTRACT = "design-system/contracts/responsive.json"
ACCESSIBILITY_CONTRACT_ID = "codestrata-accessibility-contract"
RESPONSIVE_CONTRACT_ID = "codestrata-responsive-contract"
CONTRACT_VERSION = "1.0"

TOKEN_CATALOG = "design-system/tokens/catalog.json"
TOKEN_CSS = "design-system/tokens/tokens.css"
ACCESSIBILITY_RULES = "design-system/accessibility/rules.json"
RESPONSIVE_RULES = "design-system/responsive/rules.json"
DOCUMENTATION = "design-system/documentation/accessibility-and-responsive.md"

ENGINE_TOKENS = "engine/src/codestrata/design_system/tokens.py"
ENGINE_STYLES = "engine/src/codestrata/reporting/html_v2/styles.py"
ENGINE_RENDERER = "engine/src/codestrata/reporting/html_v2/renderer.py"

EIR_STYLES = (
    "platform/src/codestrata_platform/intelligence_reporting/"
    "presentation/static_html/styles.py"
)
EIR_RENDERER = (
    "platform/src/codestrata_platform/intelligence_reporting/"
    "presentation/static_html/renderer.py"
)

DOCS_CONFIG = "docs/.vitepress/config.ts"
DOCS_TOKENS_CSS = "docs/.vitepress/theme/tokens.css"
DOCS_CUSTOM_CSS = "docs/.vitepress/theme/custom.css"
DOCS_COMPONENTS_CSS = "docs/.vitepress/theme/components.css"
DOCS_HOME_LINK = "docs/.vitepress/theme/CsDocsHomeLink.vue"
DOCS_FOOTER = "docs/.vitepress/theme/CsFooter.vue"
DOCS_DIST = "docs/.vitepress/dist"
DOCS_BROWSER_SCRIPT = "docs/scripts/a11y-responsive-validate.mjs"

VSCODE_PACKAGE = "vscode-plugin/package.json"
VSCODE_STATUS_BAR = "vscode-plugin/src/ui/statusBar.ts"
VSCODE_FINDINGS_TREE = "vscode-plugin/src/views/findingsTree.ts"
VSCODE_RECOMMENDATIONS_TREE = "vscode-plugin/src/views/recommendationsTree.ts"
VSCODE_ACTIVITY_ICON = "vscode-plugin/media/codestrata-activity.svg"
VSCODE_SOURCE_ROOT = "vscode-plugin/src"

MARKETPLACE_README = "vscode-plugin/README.md"
MARKETPLACE_GENERATOR = "vscode-plugin/scripts/generate_marketplace_visuals.py"
MARKETPLACE_MANIFEST = "vscode-plugin/policies/marketplace_visual_manifest.json"
MARKETPLACE_MEDIA = "vscode-plugin/media"

# Deployment stays owned by Slice 14.12.
DEPLOYMENT_PATHS: tuple[str, ...] = (
    "docs/wrangler.toml",
    "wrangler.toml",
    "docs/.vitepress/dist/_headers",
    "docs/public/_headers",
)

# Slice 14.14 must not have started.
FORBIDDEN_EPIC_15_PATHS: tuple[str, ...] = (
    "verification/epic15_start",
    "verification/epic_15",
    "tests/verification/epic15_start",
    "reports/verification/sv15-1",
)

VIEWPORT_MATRIX_PX: tuple[int, ...] = (320, 375, 390, 768, 1024, 1280, 1440)

# WCAG 2.x contrast thresholds.
NORMAL_TEXT_RATIO = 4.5
LARGE_TEXT_RATIO = 3.0
NON_TEXT_RATIO = 3.0

ALLOWED_LIMITATIONS: tuple[str, ...] = (
    "automated_structural_and_computed_checks_only_no_formal_wcag_certification",
    "browser_validation_limited_to_one_chromium_engine_on_one_os",
    "forced_colors_baseline_not_validated_on_windows_high_contrast",
    "manual_screen_reader_validation_not_performed",
    "marketplace_screenshots_remain_raster_fixtures",
    "print_pagination_not_publication_quality",
    "vscode_accessibility_delegated_to_native_host",
    "worktree_uncommitted",
)


@dataclass(frozen=True, slots=True)
class Sv1411Contract:
    """Immutable boundary contract for Slice 14.11."""

    policy_id: str = POLICY_ID
    policy_version: str = POLICY_VERSION
    design_system_version: str = "1.0"
    presentation_version: str = "1.0"
    visualization_version: str = "1.0"
    report_ia_version: str = "1.0"
    brand_asset_version: str = "1.0"
    assessment_schema_version: str = "1.2"
    extension_version: str = "0.2.0"
    wcag_target: str = "2.2_AA_oriented"
    wcag_certification_claimed: bool = False
    no_runtime_change: bool = True
    no_schema_change: bool = True
    no_report_content_change: bool = True
    no_report_ia_change: bool = True
    no_visualization_change: bool = True
    no_brand_geometry_change: bool = True
    no_deployment_change: bool = True
    start_epic_15: bool = False


def default_contract() -> Sv1411Contract:
    return Sv1411Contract()


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]

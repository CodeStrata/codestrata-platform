"""Contract for Slice 14.10 (brand assets)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "brand-assets-verification"
SCHEMA_VERSION = "1.0.0"
SV1410_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv14-10"
REPORT_JSON = "brand-assets-verification.json"
REPORT_MD = "brand-assets-verification.md"

POLICY_ID = "codestrata-brand-asset-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "design-system/policies/brand_asset_policy.json"
ASSET_CONTRACT = "design-system/contracts/assets.json"
ICON_CONTRACT = "design-system/contracts/icons.json"
TOKEN_CATALOG = "design-system/tokens/catalog.json"
DOCUMENTATION = "design-system/documentation/brand-assets.md"

GENERATOR = "scripts/generate_brand_assets.py"
RASTER_GENERATOR = "vscode-plugin/scripts/generate_marketplace_visuals.py"

BRAND_DIR = "design-system/assets/brand"
MASTER_MARK = f"{BRAND_DIR}/codestrata-mark.svg"
MASTER_WORDMARK = f"{BRAND_DIR}/codestrata-wordmark.svg"
MARK_ON_DARK = f"{BRAND_DIR}/codestrata-mark-on-dark.svg"
MARK_MONO = f"{BRAND_DIR}/codestrata-mark-mono.svg"
MARK_SIMPLIFIED = f"{BRAND_DIR}/codestrata-mark-simplified-mono.svg"
MARK_TILE_ON_DARK = f"{BRAND_DIR}/codestrata-mark-tile-on-dark.svg"
LOCKUP_ON_LIGHT = f"{BRAND_DIR}/codestrata-lockup-horizontal-on-light.svg"
LOCKUP_ON_DARK = f"{BRAND_DIR}/codestrata-lockup-horizontal-on-dark.svg"

MASTER_ASSETS: tuple[str, ...] = (
    MASTER_MARK,
    MASTER_WORDMARK,
    MARK_ON_DARK,
    MARK_MONO,
    MARK_SIMPLIFIED,
    MARK_TILE_ON_DARK,
    LOCKUP_ON_LIGHT,
    LOCKUP_ON_DARK,
)

DOCS_FAVICON = "docs/public/favicon.svg"
DOCS_MARK = "docs/public/brand/icon.svg"
DOCS_TILE = "docs/public/brand/icon-tile-dark.svg"
DOCS_LOCKUP_LIGHT = "docs/public/brand/lockup-horizontal-on-light.svg"
DOCS_LOCKUP_DARK = "docs/public/brand/lockup-horizontal-on-dark.svg"
DOCS_CONFIG = "docs/.vitepress/config.ts"
DOCS_CUSTOM_CSS = "docs/.vitepress/theme/custom.css"
DOCS_HOME_LINK = "docs/.vitepress/theme/CsDocsHomeLink.vue"

ENGINE_REPORT_MARK = "engine/src/codestrata/reporting/assets/codestrata-mark-mono.svg"
ENGINE_BRANDING = "engine/src/codestrata/reporting/branding.py"
ENGINE_RENDERER = "engine/src/codestrata/reporting/html_v2/renderer.py"
ENGINE_STYLES = "engine/src/codestrata/reporting/html_v2/styles.py"
ENGINE_PYPROJECT = "engine/pyproject.toml"
ENGINE_RESOURCES = "engine/src/codestrata/resources/__init__.py"

EIR_RENDERER = (
    "platform/src/codestrata_platform/intelligence_reporting/"
    "presentation/static_html/renderer.py"
)
EIR_STYLES = (
    "platform/src/codestrata_platform/intelligence_reporting/"
    "presentation/static_html/styles.py"
)

SWAGGER_BRAND_DIR = "platform/api/openapi/swagger/brand"
SWAGGER_MARK = f"{SWAGGER_BRAND_DIR}/icon.svg"
SWAGGER_LOCKUP_LIGHT = f"{SWAGGER_BRAND_DIR}/lockup-horizontal-on-light.svg"
SWAGGER_LOCKUP_DARK = f"{SWAGGER_BRAND_DIR}/lockup-horizontal-on-dark.svg"
SWAGGER_INDEX = "platform/api/openapi/swagger/index.html"

VSCODE_ACTIVITY = "vscode-plugin/media/codestrata-activity.svg"
VSCODE_PACKAGE = "vscode-plugin/package.json"
MARKETPLACE_ICON = "vscode-plugin/media/codestrata-icon.png"
MARKETPLACE_ICON_GOVERNANCE_COPY = (
    "governance/assets/extension-branding/codestrata-marketplace-icon-derivative-128.png"
)

EXPORT_MANIFEST = "public-export-manifest.yaml"

# (master, consumer copy) pairs that must remain byte-identical.
CONSUMER_COPIES: tuple[tuple[str, str], ...] = (
    (MASTER_MARK, DOCS_FAVICON),
    (MASTER_MARK, DOCS_MARK),
    (MARK_TILE_ON_DARK, DOCS_TILE),
    (LOCKUP_ON_LIGHT, DOCS_LOCKUP_LIGHT),
    (LOCKUP_ON_DARK, DOCS_LOCKUP_DARK),
    (MARK_MONO, ENGINE_REPORT_MARK),
    (MARK_SIMPLIFIED, VSCODE_ACTIVITY),
    (MASTER_MARK, SWAGGER_MARK),
    (LOCKUP_ON_LIGHT, SWAGGER_LOCKUP_LIGHT),
    (LOCKUP_ON_DARK, SWAGGER_LOCKUP_DARK),
)

ACTIVE_SVG_ASSETS: tuple[str, ...] = (
    *MASTER_ASSETS,
    DOCS_FAVICON,
    DOCS_MARK,
    DOCS_TILE,
    DOCS_LOCKUP_LIGHT,
    DOCS_LOCKUP_DARK,
    ENGINE_REPORT_MARK,
    VSCODE_ACTIVITY,
    SWAGGER_MARK,
    SWAGGER_LOCKUP_LIGHT,
    SWAGGER_LOCKUP_DARK,
)

ACTIVE_RASTER_ASSETS: tuple[str, ...] = (
    MARKETPLACE_ICON,
    MARKETPLACE_ICON_GOVERNANCE_COPY,
)

# Amber-era identity. Present only inside the governance archive.
LEGACY_BRAND_HEX: tuple[str, ...] = (
    "#d98a3d",
    "#4fb3a5",
    "#5c6675",
    "#8b95a5",
    "#b06a24",
    "#0f1216",
    "#6b7686",
    "#9aa3ae",
    "#0e1116",
    "#edeff2",
)

GOVERNANCE_ARCHIVE = "governance/assets"
GOVERNANCE_ARCHIVE_README = "governance/assets/README.md"

# Master strata geometry, mirrored from the asset contract for cross-checking.
MASTER_MARK_GRID = 22.0
MASTER_MARK_BARS: tuple[tuple[float, float, float, float], ...] = (
    (1.0, 3.0, 20.0, 3.0),
    (4.0, 8.0, 17.0, 3.0),
    (1.0, 13.0, 14.0, 3.0),
    (6.0, 18.0, 12.0, 3.0),
)
MASTER_FILL_TOKENS: tuple[str, ...] = ("muted", "teal_dark", "teal", "rust")

RETIRED_RASTER_REPORT_LOGO = "engine/src/codestrata/reporting/assets/codestrata-logo.png"

# Slice 14.14 must not have started.
FORBIDDEN_15_7_PATHS: tuple[str, ...] = (
    ".codestrata-artifacts/validation/suites/sv15-7",
)

ALLOWED_LIMITATIONS: tuple[str, ...] = (
    "documentation_and_extension_repositories_require_self_contained_derivative_copies",
    "engine_documentation_capture_images_not_refreshed",
    "governance_archive_retains_legacy_amber_geometry_for_history",
    "marketplace_icon_remains_raster_derivative",
    "no_browser_or_pixel_visual_validation",
    "vscode_activity_icon_uses_simplified_three_bar_reduction",
    "worktree_uncommitted",
)


@dataclass(frozen=True, slots=True)
class Sv1410Contract:
    """Immutable boundary contract for Slice 14.10."""

    policy_id: str = POLICY_ID
    policy_version: str = POLICY_VERSION
    design_system_version: str = "1.0"
    assessment_schema_version: str = "1.2"
    extension_version: str = "0.2.0"
    single_master_required: bool = True
    no_runtime_change: bool = True
    no_schema_change: bool = True
    no_report_ia_change: bool = True
    no_visualization_change: bool = True
    no_marketplace_gallery_redesign: bool = True
    start_slice_15_7: bool = False


def default_contract() -> Sv1410Contract:
    return Sv1410Contract()


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]

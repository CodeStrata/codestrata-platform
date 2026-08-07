/**
 * Community VS Code Marketplace branding policy (Slice 13.12).
 * policy_id = community-vscode-marketplace-branding-policy
 * policy_version = 1.0
 *
 * Visual reference: current codestrata.ai website (dark-first amber/slate).
 * Does not redesign website, reports, or Epic 14 design system.
 */

export const MARKETPLACE_BRANDING_POLICY_ID =
  "community-vscode-marketplace-branding-policy" as const;
export const MARKETPLACE_BRANDING_POLICY_VERSION = "1.0" as const;

export const MARKETPLACE_PRODUCT_NAME = "CodeStrata" as const;
export const MARKETPLACE_DISPLAY_NAME =
  "CodeStrata – Engineering Intelligence" as const;
export const MARKETPLACE_PUBLISHER_NAME = "codestrata" as const;
export const MARKETPLACE_EXTENSION_VERSION = "0.2.0" as const;
export const MARKETPLACE_TAGLINE =
  "Engineering decisions grounded in code." as const;

export const MARKETPLACE_GALLERY_BANNER_COLOR = "#0f1216" as const;
export const MARKETPLACE_GALLERY_BANNER_THEME = "dark" as const;

/** Deterministic Marketplace screenshot gallery order (relative media paths). */
export const MARKETPLACE_GALLERY_ORDER: readonly string[] = [
  "media/screenshot-findings.png",
  "media/screenshot-report.png",
  "media/screenshot-progress.png",
  "media/screenshot-activity.png",
  "media/screenshot-recommendations.png",
] as const;

export const MARKETPLACE_REQUIRED_ASSETS: readonly string[] = [
  "media/codestrata-icon.png",
  "media/codestrata-activity.svg",
  "media/marketplace-banner.png",
  ...MARKETPLACE_GALLERY_ORDER,
] as const;

export const MARKETPLACE_APPROVED_ASSET_TYPES: readonly string[] = [
  "png",
  "svg",
] as const;

export type MarketplaceBrandingPolicy = {
  readonly policy_id: typeof MARKETPLACE_BRANDING_POLICY_ID;
  readonly policy_version: typeof MARKETPLACE_BRANDING_POLICY_VERSION;
  readonly product_name: typeof MARKETPLACE_PRODUCT_NAME;
  readonly display_name: typeof MARKETPLACE_DISPLAY_NAME;
  readonly publisher_name: typeof MARKETPLACE_PUBLISHER_NAME;
  readonly extension_version: typeof MARKETPLACE_EXTENSION_VERSION;
  readonly supported_editor: "vscode";
  readonly visual_reference: "current_codestrata_website";
  readonly tagline: typeof MARKETPLACE_TAGLINE;
  readonly gallery_banner_color: typeof MARKETPLACE_GALLERY_BANNER_COLOR;
  readonly gallery_banner_theme: typeof MARKETPLACE_GALLERY_BANNER_THEME;
  readonly cursor_branding_allowed: false;
  readonly website_redesign_allowed: false;
  readonly report_redesign_allowed: false;
  readonly unverified_claims_allowed: false;
  readonly approved_asset_types: readonly string[];
  readonly required_marketplace_assets: readonly string[];
  readonly gallery_order: readonly string[];
  readonly limitations: readonly string[];
};

export const DEFAULT_MARKETPLACE_BRANDING_LIMITATIONS: readonly string[] = [
  "marketplace_listing_copy_complete_via_13_13",
  "clean_install_validation_complete_via_13_14",
  "cross_product_design_system_deferred_to_epic_14",
  "no_remote_marketplace_preview",
  "no_live_marketplace_upload",
  "screenshots_from_synthetic_fixtures",
  "no_full_extension_host_visual_automation",
  "worktree_uncommitted",
] as const;

export function createMarketplaceBrandingPolicy(
  limitations: readonly string[] = DEFAULT_MARKETPLACE_BRANDING_LIMITATIONS
): MarketplaceBrandingPolicy {
  return {
    policy_id: MARKETPLACE_BRANDING_POLICY_ID,
    policy_version: MARKETPLACE_BRANDING_POLICY_VERSION,
    product_name: MARKETPLACE_PRODUCT_NAME,
    display_name: MARKETPLACE_DISPLAY_NAME,
    publisher_name: MARKETPLACE_PUBLISHER_NAME,
    extension_version: MARKETPLACE_EXTENSION_VERSION,
    supported_editor: "vscode",
    visual_reference: "current_codestrata_website",
    tagline: MARKETPLACE_TAGLINE,
    gallery_banner_color: MARKETPLACE_GALLERY_BANNER_COLOR,
    gallery_banner_theme: MARKETPLACE_GALLERY_BANNER_THEME,
    cursor_branding_allowed: false,
    website_redesign_allowed: false,
    report_redesign_allowed: false,
    unverified_claims_allowed: false,
    approved_asset_types: [...MARKETPLACE_APPROVED_ASSET_TYPES],
    required_marketplace_assets: [...MARKETPLACE_REQUIRED_ASSETS],
    gallery_order: [...MARKETPLACE_GALLERY_ORDER],
    limitations: [...limitations].sort(),
  };
}

export function marketplaceBrandingPolicyToStableDict(
  policy: MarketplaceBrandingPolicy
): Record<string, unknown> {
  return {
    approved_asset_types: [...policy.approved_asset_types].sort(),
    cursor_branding_allowed: policy.cursor_branding_allowed,
    display_name: policy.display_name,
    extension_version: policy.extension_version,
    gallery_banner_color: policy.gallery_banner_color,
    gallery_banner_theme: policy.gallery_banner_theme,
    gallery_order: [...policy.gallery_order],
    limitations: [...policy.limitations].sort(),
    policy_id: policy.policy_id,
    policy_version: policy.policy_version,
    product_name: policy.product_name,
    publisher_name: policy.publisher_name,
    report_redesign_allowed: policy.report_redesign_allowed,
    required_marketplace_assets: [...policy.required_marketplace_assets].sort(),
    supported_editor: policy.supported_editor,
    tagline: policy.tagline,
    unverified_claims_allowed: policy.unverified_claims_allowed,
    visual_reference: policy.visual_reference,
    website_redesign_allowed: policy.website_redesign_allowed,
  };
}

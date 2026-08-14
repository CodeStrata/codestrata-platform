/**
 * Community VS Code Marketplace documentation policy (Slice 13.13).
 * policy_id = community-vscode-marketplace-documentation-policy
 * policy_version = 1.0
 *
 * README.md is the authoritative Marketplace-facing listing.
 * MARKETPLACE.md is the publishing/checklist guide only.
 */

export const MARKETPLACE_DOCS_POLICY_ID =
  "community-vscode-marketplace-documentation-policy" as const;
export const MARKETPLACE_DOCS_POLICY_VERSION = "1.0" as const;

export const MARKETPLACE_DOCS_EXTENSION_VERSION = "0.2.2" as const;
export const MARKETPLACE_DOCS_BRANDING_POLICY_VERSION = "1.0" as const;
export const MARKETPLACE_LISTING_AUTHORITY = "readme" as const;

export type MarketplaceDocsPolicy = {
  readonly policy_id: typeof MARKETPLACE_DOCS_POLICY_ID;
  readonly policy_version: typeof MARKETPLACE_DOCS_POLICY_VERSION;
  readonly extension_version: typeof MARKETPLACE_DOCS_EXTENSION_VERSION;
  readonly supported_editor: "vscode";
  readonly branding_policy_version: typeof MARKETPLACE_DOCS_BRANDING_POLICY_VERSION;
  readonly listing_authority: typeof MARKETPLACE_LISTING_AUTHORITY;
  readonly runtime_claims_require_verified_capability: true;
  readonly source_locality_claims_require_ai_qualification: true;
  readonly telemetry_operational_claim_allowed: false;
  readonly automatic_installation_claim_allowed: false;
  readonly cursor_claim_allowed: false;
  readonly cloud_dashboard_claim_allowed: false;
  readonly private_links_allowed: false;
  readonly screenshots_required: true;
  readonly limitations_required: true;
  readonly clean_install_validation_complete: true;
  readonly limitations: readonly string[];
};

export const DEFAULT_MARKETPLACE_DOCS_LIMITATIONS: readonly string[] = [
  "clean_install_validation_complete_via_13_14",
  "cross_product_docs_redesign_deferred_to_epic_14",
  "no_remote_marketplace_preview",
  "no_live_marketplace_upload",
  "links_not_remotely_fetched",
  "no_full_marketplace_renderer_automation",
  "worktree_uncommitted",
] as const;

/** Required H2 headings in the Marketplace README (order-sensitive). */
export const MARKETPLACE_README_REQUIRED_HEADINGS: readonly string[] = [
  "What CodeStrata Does",
  "What You Get",
  "Requirements",
  "Quick Start",
  "CLI Installation",
  "Repository Initialization",
  "Running an Assessment",
  "Assessment with AI",
  "Progress",
  "Reports",
  "Failure and Recovery",
  "CLI Compatibility",
  "Privacy and Source Locality",
  "Telemetry",
  "Security",
  "Known Limitations",
  "Support",
] as const;

export function createMarketplaceDocsPolicy(
  limitations: readonly string[] = DEFAULT_MARKETPLACE_DOCS_LIMITATIONS
): MarketplaceDocsPolicy {
  return {
    policy_id: MARKETPLACE_DOCS_POLICY_ID,
    policy_version: MARKETPLACE_DOCS_POLICY_VERSION,
    extension_version: MARKETPLACE_DOCS_EXTENSION_VERSION,
    supported_editor: "vscode",
    branding_policy_version: MARKETPLACE_DOCS_BRANDING_POLICY_VERSION,
    listing_authority: MARKETPLACE_LISTING_AUTHORITY,
    runtime_claims_require_verified_capability: true,
    source_locality_claims_require_ai_qualification: true,
    telemetry_operational_claim_allowed: false,
    automatic_installation_claim_allowed: false,
    cursor_claim_allowed: false,
    cloud_dashboard_claim_allowed: false,
    private_links_allowed: false,
    screenshots_required: true,
    limitations_required: true,
    clean_install_validation_complete: true,
    limitations: [...limitations].sort(),
  };
}

export function marketplaceDocsPolicyToStableDict(
  policy: MarketplaceDocsPolicy
): Record<string, unknown> {
  return {
    automatic_installation_claim_allowed:
      policy.automatic_installation_claim_allowed,
    branding_policy_version: policy.branding_policy_version,
    clean_install_validation_complete: policy.clean_install_validation_complete,
    cloud_dashboard_claim_allowed: policy.cloud_dashboard_claim_allowed,
    cursor_claim_allowed: policy.cursor_claim_allowed,
    extension_version: policy.extension_version,
    limitations: [...policy.limitations].sort(),
    limitations_required: policy.limitations_required,
    listing_authority: policy.listing_authority,
    policy_id: policy.policy_id,
    policy_version: policy.policy_version,
    private_links_allowed: policy.private_links_allowed,
    runtime_claims_require_verified_capability:
      policy.runtime_claims_require_verified_capability,
    screenshots_required: policy.screenshots_required,
    source_locality_claims_require_ai_qualification:
      policy.source_locality_claims_require_ai_qualification,
    supported_editor: policy.supported_editor,
    telemetry_operational_claim_allowed:
      policy.telemetry_operational_claim_allowed,
  };
}

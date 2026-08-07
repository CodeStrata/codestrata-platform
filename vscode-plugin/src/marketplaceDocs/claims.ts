/** Claim matrix helpers for Marketplace documentation (Slice 13.13). */

export type MarketplaceClaimClass =
  | "verified_current_capability"
  | "verified_limitation"
  | "optional_capability"
  | "future_not_claimed"
  | "prohibited_claim";

export type MarketplaceClaimRow = {
  readonly topic: string;
  readonly classification: MarketplaceClaimClass;
  readonly note: string;
};

export const MARKETPLACE_CLAIM_MATRIX: readonly MarketplaceClaimRow[] = [
  {
    topic: "vscode_support",
    classification: "verified_current_capability",
    note: "VS Code only Community editor extension",
  },
  {
    topic: "cursor_support",
    classification: "prohibited_claim",
    note: "Cursor product removed; must not appear in listing",
  },
  {
    topic: "cli_installation",
    classification: "verified_limitation",
    note: "Guidance-only; no automatic install",
  },
  {
    topic: "cli_compatibility",
    classification: "verified_current_capability",
    note: "Extension 0.2.0 supports CLI 0.2.x",
  },
  {
    topic: "repository_initialization",
    classification: "verified_current_capability",
    note: "User-triggered Engine-owned init",
  },
  {
    topic: "standard_assessment",
    classification: "verified_current_capability",
    note: "Local Engine assess",
  },
  {
    topic: "ai_assessment",
    classification: "optional_capability",
    note: "Engine-owned provider flow when configured",
  },
  {
    topic: "progress",
    classification: "verified_current_capability",
    note: "Indeterminate progress; no fake percentage",
  },
  {
    topic: "report",
    classification: "verified_current_capability",
    note: "Local HTML report open",
  },
  {
    topic: "recovery",
    classification: "verified_current_capability",
    note: "User-triggered guidance only",
  },
  {
    topic: "telemetry",
    classification: "verified_limitation",
    note: "Optional/default Deny; transport unavailable",
  },
  {
    topic: "analytics",
    classification: "verified_limitation",
    note: "Unavailable sink; not operational production",
  },
  {
    topic: "source_locality",
    classification: "verified_current_capability",
    note: "No Community upload; AI qualified separately",
  },
  {
    topic: "cloud_dashboard",
    classification: "prohibited_claim",
    note: "No runtime Cloud client",
  },
  {
    topic: "data_lake",
    classification: "prohibited_claim",
    note: "No Data Lake client",
  },
  {
    topic: "installation_identity",
    classification: "prohibited_claim",
    note: "No install/machine identity",
  },
  {
    topic: "automatic_remediation",
    classification: "prohibited_claim",
    note: "No autonomous code changes",
  },
  {
    topic: "clean_install_validation",
    classification: "verified_current_capability",
    note: "Clean install/update validation complete for v0.2.0 packaging",
  },
] as const;

export const FORBIDDEN_MARKETPLACE_DOC_FRAGMENTS: readonly string[] = [
  "supports cursor",
  "vscode and cursor",
  "automatically installs",
  "automatic cli installation",
  "all data always stays local",
  "nothing ever leaves your machine",
  "no network is ever used",
  "your data never leaves your machine",
  "we collect anonymous usage analytics",
  "production telemetry is operational",
  "cloud dashboard",
  "data lake sync",
  "synced insights",
  "team dashboards",
  "autonomous remediation",
  "available now on marketplace",
  "published on the marketplace",
] as const;

export const FORBIDDEN_INTERNAL_LISTING_FRAGMENTS: readonly string[] = [
  "slice 13.",
  "epic 13",
  "epic 14",
  "verification/",
  "sv13-",
  "policy_id",
  "not started",
  "todo",
  "tbd",
] as const;

export function marketplaceDocsContainForbiddenClaim(text: string): boolean {
  const lower = text.toLowerCase();
  return FORBIDDEN_MARKETPLACE_DOC_FRAGMENTS.some((f) => lower.includes(f));
}

export function marketplaceListingContainsInternalLeak(text: string): boolean {
  const lower = text.toLowerCase();
  return FORBIDDEN_INTERNAL_LISTING_FRAGMENTS.some((f) => lower.includes(f));
}

export function marketplaceClaimMatrixToStableDict(): Record<string, unknown> {
  return {
    claims: MARKETPLACE_CLAIM_MATRIX.map((row) => ({
      classification: row.classification,
      note: row.note,
      topic: row.topic,
    })),
  };
}

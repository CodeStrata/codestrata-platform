/** Forbidden Marketplace short-form claim patterns (Slice 13.12). */

export const FORBIDDEN_MARKETPLACE_CLAIM_PATTERNS: readonly string[] = [
  "fully autonomous modernization",
  "100% anonymous telemetry",
  "all code stays local",
  "all source always stays local",
  "zero data leaves",
  "no network ever",
  "automatic cli installation",
  "automatically installs",
  "supports cursor",
  "production cloud insights",
  "production telemetry",
  "guaranteed security",
  "aimf",
  "ai modernization factory",
  "codestrata cursor",
  "codestrata ai scanner",
] as const;

export function marketplaceTextContainsForbiddenClaim(text: string): boolean {
  const lower = text.toLowerCase();
  return FORBIDDEN_MARKETPLACE_CLAIM_PATTERNS.some((p) => lower.includes(p));
}

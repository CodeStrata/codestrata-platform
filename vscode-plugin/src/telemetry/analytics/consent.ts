/**
 * Consent gating for VS Code analytics (Epic 10 Slice 10.7).
 * Reuses Slice 9.13 command-local consent — no second prompt.
 */

import type { VsCodeTelemetryConsent } from "../consent";

export function isAnalyticsConstructionAllowed(
  consent: VsCodeTelemetryConsent
): boolean {
  return consent.decision === "allowed_for_session";
}

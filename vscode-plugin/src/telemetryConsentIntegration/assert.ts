/**
 * Assert helpers for consent integration invariants (Slice 13.9).
 */

import {
  isTelemetryEligibleCommand,
  operationForCommandId,
} from "./eligibility";
import {
  evaluateConsentOrdering,
  type ProductReadinessSnapshot,
} from "./ordering";

export class TelemetryConsentIntegrationError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "TelemetryConsentIntegrationError";
    this.code = code;
  }
}

/**
 * Call immediately before runTelemetryConsentPrompt on the assess path.
 * Throws when readiness is incomplete (should be unreachable in extension).
 */
export function assertConsentMayProceed(options: {
  readonly commandId: string;
  readonly readiness: ProductReadinessSnapshot;
}): void {
  if (!isTelemetryEligibleCommand(options.commandId)) {
    throw new TelemetryConsentIntegrationError(
      "command_not_eligible",
      "Telemetry consent requested for an ineligible command."
    );
  }
  const ordering = evaluateConsentOrdering(options.readiness);
  if (!ordering.consent_allowed) {
    throw new TelemetryConsentIntegrationError(
      ordering.reason,
      "Telemetry consent requested before product readiness."
    );
  }
}

/** Fresh decision per command — prior consent objects must not be reused. */
export function assertFreshConsentDecision(options: {
  readonly priorConsentReused: boolean;
  readonly persisted: boolean;
}): void {
  if (options.priorConsentReused) {
    throw new TelemetryConsentIntegrationError(
      "consent_reuse_forbidden",
      "Prior consent must not be reused across commands."
    );
  }
  if (options.persisted) {
    throw new TelemetryConsentIntegrationError(
      "consent_persistence_forbidden",
      "Consent must not be persisted."
    );
  }
}

export function integrationOperationLabel(commandId: string): string {
  return operationForCommandId(commandId) ?? "unknown";
}

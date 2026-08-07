/**
 * Readiness-before-consent ordering (Slice 13.9).
 * Consent must not appear until the product command can actually run.
 */

export const READINESS_STAGES = [
  "workspace",
  "repository_initialization",
  "compatible_cli",
  "cli_compatibility",
  "ai_confirmation",
  "telemetry_consent",
  "analytics_setup",
  "progress",
  "engine_invocation",
] as const;

export type ReadinessStage = (typeof READINESS_STAGES)[number];

export type ProductReadinessSnapshot = {
  readonly workspace_ready: boolean;
  readonly repository_initialized: boolean;
  readonly cli_compatible: boolean;
  /** True when AI confirmation is not applicable or user continued. */
  readonly ai_confirmation_satisfied: boolean;
};

export type ConsentOrderingResult = {
  readonly readiness_passed: boolean;
  readonly consent_allowed: boolean;
  readonly blocked_stage: ReadinessStage | "none";
  readonly reason:
    | "ready"
    | "workspace_unavailable"
    | "repository_not_initialized"
    | "cli_not_ready"
    | "ai_confirmation_declined";
};

/**
 * Evaluate whether command-local telemetry consent may be prompted.
 * Does not prompt — callers invoke the Slice 9.13 prompt only when allowed.
 */
export function evaluateConsentOrdering(
  snapshot: ProductReadinessSnapshot
): ConsentOrderingResult {
  if (!snapshot.workspace_ready) {
    return {
      readiness_passed: false,
      consent_allowed: false,
      blocked_stage: "workspace",
      reason: "workspace_unavailable",
    };
  }
  if (!snapshot.repository_initialized) {
    return {
      readiness_passed: false,
      consent_allowed: false,
      blocked_stage: "repository_initialization",
      reason: "repository_not_initialized",
    };
  }
  if (!snapshot.cli_compatible) {
    return {
      readiness_passed: false,
      consent_allowed: false,
      blocked_stage: "compatible_cli",
      reason: "cli_not_ready",
    };
  }
  if (!snapshot.ai_confirmation_satisfied) {
    return {
      readiness_passed: false,
      consent_allowed: false,
      blocked_stage: "ai_confirmation",
      reason: "ai_confirmation_declined",
    };
  }
  return {
    readiness_passed: true,
    consent_allowed: true,
    blocked_stage: "none",
    reason: "ready",
  };
}

export function consentOrderingToStableDict(
  result: ConsentOrderingResult
): Record<string, unknown> {
  return {
    blocked_stage: result.blocked_stage,
    consent_allowed: result.consent_allowed,
    readiness_passed: result.readiness_passed,
    reason: result.reason,
  };
}

/** Canonical stage order for documentation/diagnostics. */
export function readinessStageOrder(): readonly string[] {
  return [...READINESS_STAGES];
}

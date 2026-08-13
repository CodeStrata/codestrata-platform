/**
 * VS Code telemetry consent prompt surface (Slice 19.4 / 20.10).
 *
 * Assess path must use resolveCanonicalConsentForAssessment (Engine authority).
 * This module keeps shared UI types and a fail-closed helper without Engine client.
 */

import {
  defaultConsent,
  denyForSession,
  nonInteractiveDisabledConsent,
  type VsCodeTelemetryConsent,
} from "./consent";
import {
  evaluatePromptEligibility,
  type PromptEligibilityReason,
} from "./promptPolicy";

export type TelemetryPromptChoice =
  | "Allow"
  | "Deny"
  | "LearnMore"
  | undefined;

export type TelemetryPromptUi = {
  showConsentPrompt(
    message: string,
    allow: string,
    deny: string,
    learnMore: string
  ): Promise<TelemetryPromptChoice>;
  openLearnMore?(): Promise<void> | void;
};

export type TelemetryPreferenceStore = {
  get(key: string): unknown;
  update(key: string, value: string): Thenable<void>;
};

export type TelemetryPromptResult = {
  readonly consent: VsCodeTelemetryConsent;
  readonly prompted: boolean;
  readonly attempts: number;
  readonly reason:
    | PromptEligibilityReason
    | "prompt_failure"
    | "user_allow"
    | "user_deny"
    | "user_dismiss"
    | "learn_more_then_deny"
    | "persisted_preference";
};

/**
 * @deprecated Prefer resolveCanonicalConsentForAssessment for assess.
 * Without an Engine client, globalState Yes is never authoritative (Slice 20.10).
 */
export async function runTelemetryConsentPrompt(options: {
  commandId: string;
  interactive: boolean;
  ui?: TelemetryPromptUi;
  decisionAlreadyExplicit?: boolean;
  explicitConsent?: VsCodeTelemetryConsent;
  preferenceStore?: TelemetryPreferenceStore;
}): Promise<TelemetryPromptResult> {
  if (options.explicitConsent) {
    return {
      consent: options.explicitConsent,
      prompted: false,
      attempts: 0,
      reason: "decision_already_explicit",
    };
  }

  const eligibility = evaluatePromptEligibility({
    commandId: options.commandId,
    interactive: options.interactive,
    decisionAlreadyExplicit: options.decisionAlreadyExplicit,
  });

  if (!eligibility.eligible) {
    if (eligibility.reason === "non_interactive") {
      return {
        consent: nonInteractiveDisabledConsent(),
        prompted: false,
        attempts: 0,
        reason: "non_interactive",
      };
    }
    return {
      consent: defaultConsent(),
      prompted: false,
      attempts: 0,
      reason: eligibility.reason,
    };
  }

  // Without Engine bridge: never trust legacy globalState Yes; fail closed.
  return {
    consent: denyForSession("interactive_prompt"),
    prompted: false,
    attempts: 0,
    reason: "prompt_failure",
  };
}

export function preferenceLabel(
  state: "undecided" | "enabled" | "disabled"
): string {
  if (state === "enabled") {
    return "Enabled";
  }
  if (state === "disabled") {
    return "Disabled";
  }
  return "Not configured";
}

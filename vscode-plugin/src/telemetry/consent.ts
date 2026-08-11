/**
 * VS Code telemetry consent (Slice 19.4).
 * Explicit Yes/No may be persisted in globalState; default remains undecided/disabled.
 */

export type VsCodeTelemetryDecision =
  | "disabled_by_default"
  | "allowed_for_session"
  | "denied_for_session"
  | "non_interactive_disabled";

export type VsCodeTelemetryDecisionSource =
  | "default"
  | "interactive_prompt"
  | "explicit_command_option"
  | "non_interactive_policy"
  | "persisted_preference";

export type VsCodeTelemetryConsent = {
  readonly decision: VsCodeTelemetryDecision;
  readonly source: VsCodeTelemetryDecisionSource;
  readonly explicit: boolean;
  readonly persisted: boolean;
  readonly priorConsentReused: boolean;
  readonly transmissionAuthorized: boolean;
  readonly scope: "command";
  readonly policyVersion: "2.0";
};

export type TelemetryPreferenceState = "undecided" | "enabled" | "disabled";

export const TELEMETRY_PREFERENCE_STATE_KEY = "codestrata.telemetryPreference";

export function defaultConsent(): VsCodeTelemetryConsent {
  return {
    decision: "disabled_by_default",
    source: "default",
    explicit: false,
    persisted: false,
    priorConsentReused: false,
    transmissionAuthorized: false,
    scope: "command",
    policyVersion: "2.0",
  };
}

export function allowForSession(
  source: VsCodeTelemetryDecisionSource = "interactive_prompt",
  options?: { persisted?: boolean; priorConsentReused?: boolean }
): VsCodeTelemetryConsent {
  return {
    decision: "allowed_for_session",
    source,
    explicit: true,
    persisted: options?.persisted === true,
    priorConsentReused: options?.priorConsentReused === true,
    transmissionAuthorized: true,
    scope: "command",
    policyVersion: "2.0",
  };
}

export function denyForSession(
  source: VsCodeTelemetryDecisionSource = "interactive_prompt",
  options?: { persisted?: boolean; priorConsentReused?: boolean }
): VsCodeTelemetryConsent {
  return {
    decision: "denied_for_session",
    source,
    explicit: true,
    persisted: options?.persisted === true,
    priorConsentReused: options?.priorConsentReused === true,
    transmissionAuthorized: false,
    scope: "command",
    policyVersion: "2.0",
  };
}

export function nonInteractiveDisabledConsent(): VsCodeTelemetryConsent {
  return {
    decision: "non_interactive_disabled",
    source: "non_interactive_policy",
    explicit: true,
    persisted: false,
    priorConsentReused: false,
    transmissionAuthorized: false,
    scope: "command",
    policyVersion: "2.0",
  };
}

export function consentFromPreference(
  state: TelemetryPreferenceState
): VsCodeTelemetryConsent | null {
  if (state === "undecided") {
    return null;
  }
  if (state === "enabled") {
    return allowForSession("persisted_preference", {
      persisted: true,
      priorConsentReused: true,
    });
  }
  return denyForSession("persisted_preference", {
    persisted: true,
    priorConsentReused: true,
  });
}

export function readPreferenceState(
  get: (key: string) => unknown
): TelemetryPreferenceState {
  const raw = get(TELEMETRY_PREFERENCE_STATE_KEY);
  if (raw === "enabled" || raw === true) {
    return "enabled";
  }
  if (raw === "disabled" || raw === false) {
    return "disabled";
  }
  return "undecided";
}

export async function writePreferenceState(
  update: (key: string, value: string) => Thenable<void>,
  state: "enabled" | "disabled"
): Promise<void> {
  await update(TELEMETRY_PREFERENCE_STATE_KEY, state);
}

export function consentToStableDict(
  consent: VsCodeTelemetryConsent
): Record<string, unknown> {
  return {
    decision: consent.decision,
    explicit: consent.explicit,
    persisted: consent.persisted,
    policyVersion: consent.policyVersion,
    priorConsentReused: consent.priorConsentReused,
    scope: consent.scope,
    source: consent.source,
    transmissionAuthorized: consent.transmissionAuthorized,
  };
}

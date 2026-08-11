/**
 * VS Code telemetry consent prompt (Slice 19.4).
 * Uses injectable UI — core module does not import vscode.
 * Default = Deny. Explicit choice is persisted via preferenceStore.
 */

import {
  allowForSession,
  consentFromPreference,
  defaultConsent,
  denyForSession,
  nonInteractiveDisabledConsent,
  readPreferenceState,
  writePreferenceState,
  type TelemetryPreferenceState,
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

export const TELEMETRY_CONSENT_MESSAGE =
  "Help improve CodeStrata?\n\nShare anonymous usage and assessment metadata.\nNo source code, repository names, file paths, findings, or credentials are sent.";

export const TELEMETRY_ALLOW_LABEL = "Allow Anonymous Telemetry";
export const TELEMETRY_DENY_LABEL = "No Thanks";
export const TELEMETRY_LEARN_MORE_LABEL = "Learn More";

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

  if (options.preferenceStore) {
    const state = readPreferenceState((key) => options.preferenceStore!.get(key));
    const reused = consentFromPreference(state);
    if (reused) {
      return {
        consent: reused,
        prompted: false,
        attempts: 0,
        reason: "persisted_preference",
      };
    }
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

  if (!options.ui) {
    return {
      consent: denyForSession("interactive_prompt"),
      prompted: false,
      attempts: 0,
      reason: "prompt_failure",
    };
  }

  const persist = async (state: "enabled" | "disabled") => {
    if (!options.preferenceStore) {
      return;
    }
    try {
      await writePreferenceState(
        (key, value) => options.preferenceStore!.update(key, value),
        state
      );
    } catch {
      // Preference write failures must never block assessment.
    }
  };

  try {
    const choice = await options.ui.showConsentPrompt(
      TELEMETRY_CONSENT_MESSAGE,
      TELEMETRY_ALLOW_LABEL,
      TELEMETRY_DENY_LABEL,
      TELEMETRY_LEARN_MORE_LABEL
    );
    if (choice === "Allow") {
      await persist("enabled");
      return {
        consent: allowForSession("interactive_prompt", { persisted: true }),
        prompted: true,
        attempts: 1,
        reason: "user_allow",
      };
    }
    if (choice === "LearnMore") {
      try {
        await options.ui.openLearnMore?.();
      } catch {
        // Learn More failures must not enable telemetry.
      }
      await persist("disabled");
      return {
        consent: denyForSession("interactive_prompt", { persisted: true }),
        prompted: true,
        attempts: 1,
        reason: "learn_more_then_deny",
      };
    }
    // Deny / dismiss / undefined → explicit No (default)
    await persist("disabled");
    return {
      consent: denyForSession("interactive_prompt", { persisted: true }),
      prompted: true,
      attempts: 1,
      reason: choice === "Deny" ? "user_deny" : "user_dismiss",
    };
  } catch {
    return {
      consent: denyForSession("interactive_prompt"),
      prompted: true,
      attempts: 1,
      reason: "prompt_failure",
    };
  }
}

export function preferenceLabel(state: TelemetryPreferenceState): string {
  if (state === "enabled") {
    return "Enabled";
  }
  if (state === "disabled") {
    return "Disabled";
  }
  return "Not configured";
}

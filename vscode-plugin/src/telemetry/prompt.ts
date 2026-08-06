/**
 * VS Code telemetry consent prompt (Slice 9.13).
 * Uses injectable UI — core module does not import vscode.
 * Default = Deny. Never persists.
 */

import {
  allowForSession,
  defaultConsent,
  denyForSession,
  nonInteractiveDisabledConsent,
  type VsCodeTelemetryConsent,
} from "./consent";
import {
  evaluatePromptEligibility,
  type PromptEligibilityReason,
} from "./promptPolicy";

export type TelemetryPromptChoice = "Allow" | "Deny" | undefined;

export type TelemetryPromptUi = {
  showConsentPrompt(message: string, allow: string, deny: string): Promise<TelemetryPromptChoice>;
};

export type TelemetryPromptResult = {
  readonly consent: VsCodeTelemetryConsent;
  readonly prompted: boolean;
  readonly attempts: number;
  readonly reason: PromptEligibilityReason | "prompt_failure" | "user_allow" | "user_deny" | "user_dismiss";
};

export const TELEMETRY_CONSENT_MESSAGE =
  "Allow privacy-safe anonymous product telemetry for this CodeStrata command only? Nothing is saved.";

export async function runTelemetryConsentPrompt(options: {
  commandId: string;
  interactive: boolean;
  ui?: TelemetryPromptUi;
  decisionAlreadyExplicit?: boolean;
  explicitConsent?: VsCodeTelemetryConsent;
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

  if (!options.ui) {
    return {
      consent: denyForSession("interactive_prompt"),
      prompted: false,
      attempts: 0,
      reason: "prompt_failure",
    };
  }

  try {
    const choice = await options.ui.showConsentPrompt(
      TELEMETRY_CONSENT_MESSAGE,
      "Allow",
      "Deny"
    );
    if (choice === "Allow") {
      return {
        consent: allowForSession("interactive_prompt"),
        prompted: true,
        attempts: 1,
        reason: "user_allow",
      };
    }
    if (choice === "Deny") {
      return {
        consent: denyForSession("interactive_prompt"),
        prompted: true,
        attempts: 1,
        reason: "user_deny",
      };
    }
    // Dismiss / undefined → default Deny (explicit denial for this command)
    return {
      consent: denyForSession("interactive_prompt"),
      prompted: true,
      attempts: 1,
      reason: "user_dismiss",
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

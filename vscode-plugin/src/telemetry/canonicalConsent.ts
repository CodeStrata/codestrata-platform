/**
 * Canonical Engine-owned consent gate for VS Code assess (Slice 20.10).
 *
 * globalState is UX cache only — never overrides Engine CODESTRATA_HOME state.
 * Legacy extension "enabled" without Engine V2 must re-consent (no grandfathering).
 */

import {
  engineConsentFailureMessage,
  queryEngineConsentStatus,
  runEngineTelemetryDeclineUpgrade,
  runEngineTelemetryDisable,
  runEngineTelemetryEnable,
  type EngineConsentCliRunner,
  type EngineConsentState,
  type EngineConsentStatus,
} from "../engine/telemetryConsentContract";
import {
  allowForSession,
  defaultConsent,
  denyForSession,
  nonInteractiveDisabledConsent,
  writePreferenceState,
  type VsCodeTelemetryConsent,
} from "./consent";
import {
  evaluatePromptEligibility,
  type PromptEligibilityReason,
} from "./promptPolicy";
import type {
  TelemetryPreferenceStore,
  TelemetryPromptResult,
  TelemetryPromptUi,
} from "./prompt";

export const TELEMETRY_CONSENT_MESSAGE =
  "Help improve CodeStrata?\n\n" +
  "Share anonymous usage and privacy-safe assessment insights.\n" +
  "Source code and repository identity stay local. This does not publish reports.";

export const TELEMETRY_UPGRADE_MESSAGE =
  "Enable privacy-safe assessment insights?\n\n" +
  "Lifecycle usage telemetry stays on. Source code and repository identity stay local. " +
  "This does not publish reports.";

export const TELEMETRY_ALLOW_LABEL = "Allow";
export const TELEMETRY_DENY_LABEL = "No Thanks";
export const TELEMETRY_LEARN_MORE_LABEL = "Learn More";
export const TELEMETRY_UPGRADE_ALLOW_LABEL = "Enable Insights";
export const TELEMETRY_UPGRADE_DENY_LABEL = "Keep Current";

export type CanonicalConsentGateResult = TelemetryPromptResult & {
  readonly engineState: EngineConsentState | "unknown";
  readonly consentCommandError?: string;
};

async function cacheUxPreference(
  store: TelemetryPreferenceStore | undefined,
  state: "enabled" | "disabled"
): Promise<void> {
  if (!store) {
    return;
  }
  try {
    await writePreferenceState(
      (key, value) => store.update(key, value),
      state
    );
  } catch {
    // UX cache failures must never block assessment.
  }
}

function resultFromEngine(
  status: EngineConsentStatus,
  extras?: Partial<CanonicalConsentGateResult>
): CanonicalConsentGateResult {
  if (status.state === "v2_yes") {
    return {
      consent: allowForSession("persisted_preference", {
        persisted: true,
        priorConsentReused: true,
      }),
      prompted: false,
      attempts: 0,
      reason: "persisted_preference",
      engineState: status.state,
      ...extras,
    };
  }
  if (status.state === "v1_yes") {
    // Extension-local analytics may proceed; Community amd stays Engine-gated OFF.
    return {
      consent: allowForSession("persisted_preference", {
        persisted: true,
        priorConsentReused: true,
      }),
      prompted: false,
      attempts: 0,
      reason: "persisted_preference",
      engineState: status.state,
      ...extras,
    };
  }
  if (status.state === "disabled") {
    return {
      consent: denyForSession("persisted_preference", {
        persisted: true,
        priorConsentReused: true,
      }),
      prompted: false,
      attempts: 0,
      reason: "persisted_preference",
      engineState: status.state,
      ...extras,
    };
  }
  return {
    consent: defaultConsent(),
    prompted: false,
    attempts: 0,
    reason: "decision_already_explicit",
    engineState: status.state,
    ...extras,
  };
}

async function promptFresh(
  ui: TelemetryPromptUi
): Promise<"Allow" | "Deny" | "LearnMore" | "Dismiss"> {
  const choice = await ui.showConsentPrompt(
    TELEMETRY_CONSENT_MESSAGE,
    TELEMETRY_ALLOW_LABEL,
    TELEMETRY_DENY_LABEL,
    TELEMETRY_LEARN_MORE_LABEL
  );
  if (choice === "Allow") {
    return "Allow";
  }
  if (choice === "LearnMore") {
    return "LearnMore";
  }
  if (choice === "Deny") {
    return "Deny";
  }
  return "Dismiss";
}

async function promptUpgrade(
  ui: TelemetryPromptUi
): Promise<"Allow" | "Deny" | "Dismiss"> {
  const choice = await ui.showConsentPrompt(
    TELEMETRY_UPGRADE_MESSAGE,
    TELEMETRY_UPGRADE_ALLOW_LABEL,
    TELEMETRY_UPGRADE_DENY_LABEL,
    TELEMETRY_LEARN_MORE_LABEL
  );
  if (choice === "Allow") {
    return "Allow";
  }
  if (choice === "Deny") {
    return "Deny";
  }
  return "Dismiss";
}

/**
 * Resolve Community consent for assess using Engine as source of truth.
 *
 * --telemetry-allow is intentionally never injected on assess (Slice 20.9 + 20.10).
 */
export async function resolveCanonicalConsentForAssessment(options: {
  commandId: string;
  interactive: boolean;
  engineClient: EngineConsentCliRunner;
  ui?: TelemetryPromptUi;
  preferenceStore?: TelemetryPreferenceStore;
  decisionAlreadyExplicit?: boolean;
  explicitConsent?: VsCodeTelemetryConsent;
  onUserMessage?: (message: string) => void;
}): Promise<CanonicalConsentGateResult> {
  if (options.explicitConsent) {
    return {
      consent: options.explicitConsent,
      prompted: false,
      attempts: 0,
      reason: "decision_already_explicit",
      engineState: "unknown",
    };
  }

  const eligibility = evaluatePromptEligibility({
    commandId: options.commandId,
    interactive: options.interactive,
    decisionAlreadyExplicit: options.decisionAlreadyExplicit,
  });

  const queried = await queryEngineConsentStatus(options.engineClient);

  // Status failure: fail-safe — no Community collection; do not trust stale globalState Yes.
  if (!queried.ok) {
    await cacheUxPreference(options.preferenceStore, "disabled");
    options.onUserMessage?.(engineConsentFailureMessage("status"));
    if (!eligibility.eligible) {
      if (eligibility.reason === "non_interactive") {
        return {
          consent: nonInteractiveDisabledConsent(),
          prompted: false,
          attempts: 0,
          reason: "non_interactive",
          engineState: "unknown",
          consentCommandError: queried.reason,
        };
      }
      return {
        consent: defaultConsent(),
        prompted: false,
        attempts: 0,
        reason: eligibility.reason,
        engineState: "unknown",
        consentCommandError: queried.reason,
      };
    }
    // Interactive: offer fresh Engine enable path (still fail-closed if enable fails).
    if (!options.ui) {
      return {
        consent: denyForSession("interactive_prompt"),
        prompted: false,
        attempts: 0,
        reason: "prompt_failure",
        engineState: "unknown",
        consentCommandError: queried.reason,
      };
    }
    try {
      const choice = await promptFresh(options.ui);
      if (choice === "Allow") {
        const enabled = await runEngineTelemetryEnable(options.engineClient);
        if (!enabled.ok) {
          options.onUserMessage?.(engineConsentFailureMessage("enable"));
          await cacheUxPreference(options.preferenceStore, "disabled");
          return {
            consent: denyForSession("interactive_prompt"),
            prompted: true,
            attempts: 1,
            reason: "user_allow",
            engineState: "unknown",
            consentCommandError: "enable_failed",
          };
        }
        await cacheUxPreference(options.preferenceStore, "enabled");
        return {
          consent: allowForSession("interactive_prompt", { persisted: true }),
          prompted: true,
          attempts: 1,
          reason: "user_allow",
          engineState: "v2_yes",
        };
      }
      if (choice === "LearnMore") {
        try {
          await options.ui.openLearnMore?.();
        } catch {
          // ignore
        }
      }
      // Deny / dismiss / Learn More → attempt Engine disable only for explicit Deny.
      if (choice === "Deny") {
        const disabled = await runEngineTelemetryDisable(options.engineClient);
        if (!disabled.ok) {
          options.onUserMessage?.(engineConsentFailureMessage("disable"));
        }
        await cacheUxPreference(options.preferenceStore, "disabled");
        return {
          consent: denyForSession("interactive_prompt", { persisted: true }),
          prompted: true,
          attempts: 1,
          reason: "user_deny",
          engineState: disabled.ok ? "disabled" : "unknown",
          consentCommandError: disabled.ok ? undefined : "disable_failed",
        };
      }
      await cacheUxPreference(options.preferenceStore, "disabled");
      return {
        consent: denyForSession("interactive_prompt"),
        prompted: true,
        attempts: 1,
        reason: choice === "LearnMore" ? "learn_more_then_deny" : "user_dismiss",
        engineState: "unknown",
      };
    } catch {
      return {
        consent: denyForSession("interactive_prompt"),
        prompted: true,
        attempts: 1,
        reason: "prompt_failure",
        engineState: "unknown",
      };
    }
  }

  const status = queried.status;

  // Sync UX cache from Engine (never the reverse).
  if (status.state === "v2_yes" || status.state === "v1_yes") {
    await cacheUxPreference(options.preferenceStore, "enabled");
  } else if (status.state === "disabled") {
    await cacheUxPreference(options.preferenceStore, "disabled");
  }

  if (status.state === "v2_yes" || status.state === "disabled") {
    return resultFromEngine(status);
  }

  if (status.state === "v1_yes") {
    if (
      status.shouldPromptV2Upgrade &&
      eligibility.eligible &&
      options.ui &&
      options.interactive
    ) {
      try {
        const choice = await promptUpgrade(options.ui);
        if (choice === "Allow") {
          const enabled = await runEngineTelemetryEnable(options.engineClient);
          if (!enabled.ok) {
            options.onUserMessage?.(engineConsentFailureMessage("enable"));
            // Keep V1 lifecycle; do not pretend V2.
            return resultFromEngine(status, {
              prompted: true,
              attempts: 1,
              reason: "user_allow",
              consentCommandError: "enable_failed",
            });
          }
          await cacheUxPreference(options.preferenceStore, "enabled");
          return {
            consent: allowForSession("interactive_prompt", { persisted: true }),
            prompted: true,
            attempts: 1,
            reason: "user_allow",
            engineState: "v2_yes",
          };
        }
        if (choice === "Deny") {
          const declined = await runEngineTelemetryDeclineUpgrade(
            options.engineClient
          );
          if (!declined.ok) {
            options.onUserMessage?.(
              engineConsentFailureMessage("decline-upgrade")
            );
          }
          return {
            consent: allowForSession("persisted_preference", {
              persisted: true,
              priorConsentReused: true,
            }),
            prompted: true,
            attempts: 1,
            reason: "user_deny",
            engineState: "v1_yes",
            consentCommandError: declined.ok
              ? undefined
              : "decline_upgrade_failed",
          };
        }
        // Dismiss: keep V1, do not mark decline (may ask again later).
        return {
          ...resultFromEngine(status),
          prompted: true,
          attempts: 1,
          reason: "user_dismiss",
        };
      } catch {
        return {
          ...resultFromEngine(status),
          prompted: true,
          attempts: 1,
          reason: "prompt_failure",
        };
      }
    }
    return resultFromEngine(status);
  }

  // UNDECIDED — never grandfather extension-local Yes.
  if (!eligibility.eligible) {
    if (eligibility.reason === "non_interactive") {
      return {
        consent: nonInteractiveDisabledConsent(),
        prompted: false,
        attempts: 0,
        reason: "non_interactive",
        engineState: "undecided",
      };
    }
    return {
      consent: defaultConsent(),
      prompted: false,
      attempts: 0,
      reason: eligibility.reason as PromptEligibilityReason,
      engineState: "undecided",
    };
  }

  if (!options.ui) {
    return {
      consent: denyForSession("interactive_prompt"),
      prompted: false,
      attempts: 0,
      reason: "prompt_failure",
      engineState: "undecided",
    };
  }

  try {
    const choice = await promptFresh(options.ui);
    if (choice === "Allow") {
      const enabled = await runEngineTelemetryEnable(options.engineClient);
      if (!enabled.ok) {
        options.onUserMessage?.(engineConsentFailureMessage("enable"));
        await cacheUxPreference(options.preferenceStore, "disabled");
        return {
          consent: denyForSession("interactive_prompt"),
          prompted: true,
          attempts: 1,
          reason: "user_allow",
          engineState: "undecided",
          consentCommandError: "enable_failed",
        };
      }
      await cacheUxPreference(options.preferenceStore, "enabled");
      return {
        consent: allowForSession("interactive_prompt", { persisted: true }),
        prompted: true,
        attempts: 1,
        reason: "user_allow",
        engineState: "v2_yes",
      };
    }
    if (choice === "LearnMore") {
      try {
        await options.ui.openLearnMore?.();
      } catch {
        // ignore
      }
    }
    if (choice === "Deny") {
      const disabled = await runEngineTelemetryDisable(options.engineClient);
      if (!disabled.ok) {
        options.onUserMessage?.(engineConsentFailureMessage("disable"));
        await cacheUxPreference(options.preferenceStore, "disabled");
        return {
          consent: denyForSession("interactive_prompt"),
          prompted: true,
          attempts: 1,
          reason: "user_deny",
          engineState: "undecided",
          consentCommandError: "disable_failed",
        };
      }
      await cacheUxPreference(options.preferenceStore, "disabled");
      return {
        consent: denyForSession("interactive_prompt", { persisted: true }),
        prompted: true,
        attempts: 1,
        reason: "user_deny",
        engineState: "disabled",
      };
    }
    // Dismiss / Learn More without Deny → leave UNDECIDED (no accidental Yes).
    return {
      consent: denyForSession("interactive_prompt"),
      prompted: true,
      attempts: 1,
      reason: choice === "LearnMore" ? "learn_more_then_deny" : "user_dismiss",
      engineState: "undecided",
    };
  } catch {
    return {
      consent: denyForSession("interactive_prompt"),
      prompted: true,
      attempts: 1,
      reason: "prompt_failure",
      engineState: "undecided",
    };
  }
}

export function preferenceLabelFromEngineState(
  state: EngineConsentState | "unknown"
): string {
  if (state === "v2_yes") {
    return "Enabled (v2)";
  }
  if (state === "v1_yes") {
    return "Enabled (legacy v1)";
  }
  if (state === "disabled") {
    return "Disabled";
  }
  if (state === "undecided") {
    return "Not configured";
  }
  return "Unknown";
}

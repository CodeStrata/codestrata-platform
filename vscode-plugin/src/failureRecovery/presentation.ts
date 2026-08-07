/**
 * Present failure recovery guidance (Slice 13.8).
 * Never auto-executes recovery actions.
 */

import { resolveRecoveryGuidance, type RecoveryGuidance } from "./catalog";
import {
  createFailureRecoveryResult,
  type FailureRecoveryResult,
} from "./results";

export type RecoveryNotificationHost = {
  readonly showErrorMessage: (
    message: string,
    ...actions: string[]
  ) => Thenable<string | undefined>;
  readonly showWarningMessage: (
    message: string,
    ...actions: string[]
  ) => Thenable<string | undefined>;
  readonly showInformationMessage: (
    message: string,
    ...actions: string[]
  ) => Thenable<string | undefined>;
  readonly executeCommand?: (commandId: string) => Thenable<unknown>;
  readonly appendOutputLine?: (line: string) => void;
};

/**
 * Resolve guidance and optionally present it.
 * Recovery commands run only when the user selects an action label.
 */
export async function presentFailureRecovery(options: {
  readonly failureCategory: string;
  readonly host?: RecoveryNotificationHost;
  /** When false, resolve only (no UI). Default true when host provided. */
  readonly present?: boolean;
  /** Override message when caller already has a bounded message. */
  readonly messageOverride?: string;
}): Promise<{
  readonly guidance: RecoveryGuidance;
  readonly result: FailureRecoveryResult;
}> {
  const guidance = resolveRecoveryGuidance(options.failureCategory);
  const present = options.present !== false && options.host !== undefined;

  if (!present || !options.host) {
    return {
      guidance,
      result: createFailureRecoveryResult({
        status:
          guidance.recovery_action === "none" ? "no_action" : "presented",
        failure_domain: guidance.failure_domain,
        failure_category: guidance.failure_category,
        ownership: guidance.ownership,
        recovery_action: guidance.recovery_action,
        workflow_recovery_flag: guidance.workflow_recovery_flag,
        action_dispatched: false,
        primary_result_preserved: guidance.primary_result_preserved,
        user_action_required: guidance.recovery_action !== "none",
        limitations: guidance.limitations,
      }),
    };
  }

  const host = options.host;
  const message = options.messageOverride ?? guidance.user_message;
  host.appendOutputLine?.(message);

  const actions =
    guidance.action_label && guidance.command_id
      ? [guidance.action_label]
      : guidance.action_label && guidance.recovery_action === "select_workspace"
        ? [] // no dispatchable command
        : guidance.action_label
          ? [guidance.action_label]
          : [];

  const show =
    guidance.severity === "error"
      ? host.showErrorMessage
      : guidance.severity === "warning"
        ? host.showWarningMessage
        : host.showInformationMessage;

  const choice = await show(message, ...actions);

  if (!choice) {
    return {
      guidance,
      result: createFailureRecoveryResult({
        status:
          guidance.recovery_action === "none" ? "no_action" : "user_declined",
        failure_domain: guidance.failure_domain,
        failure_category: guidance.failure_category,
        ownership: guidance.ownership,
        recovery_action: guidance.recovery_action,
        workflow_recovery_flag: guidance.workflow_recovery_flag,
        action_dispatched: false,
        primary_result_preserved: guidance.primary_result_preserved,
        user_action_required: guidance.recovery_action !== "none",
        limitations: guidance.limitations,
      }),
    };
  }

  // Never auto-execute: only dispatch when user selected the labeled action.
  if (
    choice === guidance.action_label &&
    guidance.command_id &&
    host.executeCommand
  ) {
    try {
      await host.executeCommand(guidance.command_id);
      return {
        guidance,
        result: createFailureRecoveryResult({
          status: "user_action_selected",
          failure_domain: guidance.failure_domain,
          failure_category: guidance.failure_category,
          ownership: guidance.ownership,
          recovery_action: guidance.recovery_action,
          workflow_recovery_flag: guidance.workflow_recovery_flag,
          action_dispatched: true,
          primary_result_preserved: guidance.primary_result_preserved,
          user_action_required: true,
          limitations: guidance.limitations,
        }),
      };
    } catch {
      return {
        guidance,
        result: createFailureRecoveryResult({
          status: "action_dispatch_failed",
          failure_domain: guidance.failure_domain,
          failure_category: guidance.failure_category,
          ownership: guidance.ownership,
          recovery_action: guidance.recovery_action,
          workflow_recovery_flag: guidance.workflow_recovery_flag,
          action_dispatched: false,
          primary_result_preserved: guidance.primary_result_preserved,
          user_action_required: true,
          limitations: guidance.limitations,
        }),
      };
    }
  }

  return {
    guidance,
    result: createFailureRecoveryResult({
      status: "presented",
      failure_domain: guidance.failure_domain,
      failure_category: guidance.failure_category,
      ownership: guidance.ownership,
      recovery_action: guidance.recovery_action,
      workflow_recovery_flag: guidance.workflow_recovery_flag,
      action_dispatched: false,
      primary_result_preserved: guidance.primary_result_preserved,
      user_action_required: guidance.recovery_action !== "none",
      limitations: guidance.limitations,
    }),
  };
}

/** True when recovery must not rewrite a successful primary result. */
export function isSecondaryFailureCategory(category: string): boolean {
  const g = resolveRecoveryGuidance(category);
  return g.ownership === "secondary";
}

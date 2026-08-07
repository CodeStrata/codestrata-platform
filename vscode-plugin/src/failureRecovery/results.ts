/** Typed failure-recovery results (Slice 13.8). */

import type {
  FailureDomain,
  FailureOwnership,
  RecoveryAction,
  WorkflowRecoveryFlag,
} from "./categories";
import { DEFAULT_RECOVERY_LIMITATIONS } from "./policy";

export type FailureRecoveryResultStatus =
  | "presented"
  | "user_action_selected"
  | "user_declined"
  | "no_action"
  | "action_dispatch_failed"
  | "skipped_success";

export type FailureRecoveryResult = {
  readonly status: FailureRecoveryResultStatus;
  readonly failure_domain: FailureDomain;
  readonly failure_category: string;
  readonly ownership: FailureOwnership;
  readonly recovery_action: RecoveryAction;
  readonly workflow_recovery_flag: WorkflowRecoveryFlag;
  readonly auto_execute: false;
  readonly action_dispatched: boolean;
  readonly primary_result_preserved: boolean;
  readonly user_action_required: boolean;
  readonly limitations: readonly string[];
};

export function createFailureRecoveryResult(
  partial: Omit<FailureRecoveryResult, "auto_execute" | "limitations"> & {
    readonly limitations?: readonly string[];
  }
): FailureRecoveryResult {
  return {
    ...partial,
    auto_execute: false,
    limitations: [
      ...(partial.limitations ?? DEFAULT_RECOVERY_LIMITATIONS),
    ].sort(),
  };
}

export function failureRecoveryResultToStableDict(
  result: FailureRecoveryResult
): Record<string, unknown> {
  return {
    action_dispatched: result.action_dispatched,
    auto_execute: result.auto_execute,
    failure_category: result.failure_category,
    failure_domain: result.failure_domain,
    limitations: [...result.limitations].sort(),
    ownership: result.ownership,
    primary_result_preserved: result.primary_result_preserved,
    recovery_action: result.recovery_action,
    status: result.status,
    user_action_required: result.user_action_required,
    workflow_recovery_flag: result.workflow_recovery_flag,
  };
}

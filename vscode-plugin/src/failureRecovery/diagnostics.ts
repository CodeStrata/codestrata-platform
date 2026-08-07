/** Privacy-safe failure-recovery diagnostics (Slice 13.8). */

import { RECOVERY_POLICY_VERSION } from "./policy";
import type { FailureRecoveryResult } from "./results";
import type { RecoveryGuidance } from "./catalog";

export type FailureRecoveryDiagnostics = {
  readonly recovery_policy_version: typeof RECOVERY_POLICY_VERSION;
  readonly operation: "present_recovery";
  readonly failure_domain: string;
  readonly failure_category: string;
  readonly ownership: string;
  readonly recovery_action: string;
  readonly workflow_recovery_flag: string;
  readonly auto_execute: false;
  readonly action_dispatched: boolean;
  readonly primary_result_preserved: boolean;
  readonly user_action_required: boolean;
  readonly telemetry_invoked: false;
  readonly analytics_invoked: false;
  readonly limitations: readonly string[];
};

const FORBIDDEN_DIAGNOSTIC_KEYS = [
  "path",
  "uri",
  "workspace",
  "stdout",
  "stderr",
  "stack",
  "exception",
  "credential",
  "password",
  "token",
  "api_key",
  "html",
  "source",
  "environment",
  "timestamp",
  "mtime",
] as const;

export function diagnosticsFromGuidance(
  guidance: RecoveryGuidance,
  options?: {
    readonly actionDispatched?: boolean;
    readonly status?: string;
  }
): FailureRecoveryDiagnostics {
  return {
    recovery_policy_version: RECOVERY_POLICY_VERSION,
    operation: "present_recovery",
    failure_domain: guidance.failure_domain,
    failure_category: guidance.failure_category,
    ownership: guidance.ownership,
    recovery_action: guidance.recovery_action,
    workflow_recovery_flag: guidance.workflow_recovery_flag,
    auto_execute: false,
    action_dispatched: options?.actionDispatched === true,
    primary_result_preserved: guidance.primary_result_preserved,
    user_action_required: guidance.recovery_action !== "none",
    telemetry_invoked: false,
    analytics_invoked: false,
    limitations: [...guidance.limitations].sort(),
  };
}

export function diagnosticsFromResult(
  result: FailureRecoveryResult
): FailureRecoveryDiagnostics {
  return {
    recovery_policy_version: RECOVERY_POLICY_VERSION,
    operation: "present_recovery",
    failure_domain: result.failure_domain,
    failure_category: result.failure_category,
    ownership: result.ownership,
    recovery_action: result.recovery_action,
    workflow_recovery_flag: result.workflow_recovery_flag,
    auto_execute: false,
    action_dispatched: result.action_dispatched,
    primary_result_preserved: result.primary_result_preserved,
    user_action_required: result.user_action_required,
    telemetry_invoked: false,
    analytics_invoked: false,
    limitations: [...result.limitations].sort(),
  };
}

export function failureRecoveryDiagnosticsToStableDict(
  diagnostics: FailureRecoveryDiagnostics
): Record<string, unknown> {
  return {
    action_dispatched: diagnostics.action_dispatched,
    analytics_invoked: diagnostics.analytics_invoked,
    auto_execute: diagnostics.auto_execute,
    failure_category: diagnostics.failure_category,
    failure_domain: diagnostics.failure_domain,
    limitations: [...diagnostics.limitations].sort(),
    operation: diagnostics.operation,
    ownership: diagnostics.ownership,
    primary_result_preserved: diagnostics.primary_result_preserved,
    recovery_action: diagnostics.recovery_action,
    recovery_policy_version: diagnostics.recovery_policy_version,
    telemetry_invoked: diagnostics.telemetry_invoked,
    user_action_required: diagnostics.user_action_required,
    workflow_recovery_flag: diagnostics.workflow_recovery_flag,
  };
}

export function recoveryDiagnosticsContainForbiddenKeys(
  value: Record<string, unknown>
): boolean {
  const blob = JSON.stringify(value).toLowerCase();
  if (blob.includes("/users/") || blob.includes("file://")) {
    return true;
  }
  for (const key of FORBIDDEN_DIAGNOSTIC_KEYS) {
    if (Object.prototype.hasOwnProperty.call(value, key)) {
      return true;
    }
  }
  return false;
}

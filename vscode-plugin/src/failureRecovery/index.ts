/** Slice 13.8 failure-recovery public exports. */

export {
  RECOVERY_POLICY_ID,
  RECOVERY_POLICY_VERSION,
  DEFAULT_RECOVERY_LIMITATIONS,
  createFailureRecoveryPolicy,
  failureRecoveryPolicyToStableDict,
  type FailureRecoveryPolicy,
} from "./policy";

export {
  FAILURE_DOMAINS,
  FAILURE_OWNERSHIPS,
  RECOVERY_ACTIONS,
  RECOVERY_ACTION_LABELS,
  RECOVERY_ACTION_COMMANDS,
  WORKFLOW_RECOVERY_FLAGS,
  type FailureDomain,
  type FailureOwnership,
  type RecoveryAction,
  type WorkflowRecoveryFlag,
} from "./categories";

export {
  resolveRecoveryGuidance,
  knownFailureCategories,
  type RecoveryGuidance,
} from "./catalog";

export {
  createFailureRecoveryResult,
  failureRecoveryResultToStableDict,
  type FailureRecoveryResult,
  type FailureRecoveryResultStatus,
} from "./results";

export {
  diagnosticsFromGuidance,
  diagnosticsFromResult,
  failureRecoveryDiagnosticsToStableDict,
  recoveryDiagnosticsContainForbiddenKeys,
  type FailureRecoveryDiagnostics,
} from "./diagnostics";

export {
  presentFailureRecovery,
  isSecondaryFailureCategory,
  type RecoveryNotificationHost,
} from "./presentation";

// vscodeHost is imported by extension only — do not re-export here
// so unit tests can load the domain package without the `vscode` module.

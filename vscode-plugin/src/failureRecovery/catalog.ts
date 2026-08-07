/**
 * Deterministic failure → recovery catalog (Slice 13.8).
 * Maps known result categories from Slices 13.1–13.7.
 */

import {
  RECOVERY_ACTION_COMMANDS,
  RECOVERY_ACTION_LABELS,
  type FailureDomain,
  type FailureOwnership,
  type RecoveryAction,
  type WorkflowRecoveryFlag,
} from "./categories";
import { DEFAULT_RECOVERY_LIMITATIONS } from "./policy";

export type RecoveryGuidance = {
  readonly failure_domain: FailureDomain;
  readonly failure_category: string;
  readonly ownership: FailureOwnership;
  readonly recovery_action: RecoveryAction;
  readonly workflow_recovery_flag: WorkflowRecoveryFlag;
  /** What failed (privacy-safe). */
  readonly what_failed: string;
  /** Why it failed (privacy-safe; no paths/stdout). */
  readonly why_failed: string;
  /** What the user should do next. */
  readonly next_step: string;
  /** Combined user-facing message. */
  readonly user_message: string;
  readonly action_label: string | undefined;
  readonly command_id: string | undefined;
  readonly auto_execute: false;
  readonly primary_result_preserved: boolean;
  readonly severity: "error" | "warning" | "info";
  readonly limitations: readonly string[];
};

type CatalogEntry = {
  readonly failure_domain: FailureDomain;
  readonly ownership: FailureOwnership;
  readonly recovery_action: RecoveryAction;
  readonly what_failed: string;
  readonly why_failed: string;
  readonly next_step: string;
  readonly severity: "error" | "warning" | "info";
  readonly primary_result_preserved?: boolean;
};

const CATALOG: Readonly<Record<string, CatalogEntry>> = {
  workspace_unavailable: {
    failure_domain: "workspace",
    ownership: "primary",
    recovery_action: "select_workspace",
    what_failed: "Workspace selection",
    why_failed: "No local workspace folder is available for CodeStrata.",
    next_step: "Open a local repository folder, then try again.",
    severity: "error",
  },
  workspace_unsupported: {
    failure_domain: "workspace",
    ownership: "primary",
    recovery_action: "select_workspace",
    what_failed: "Workspace trust or locality",
    why_failed: "This workspace cannot run CodeStrata Engine safely.",
    next_step: "Use a trusted local folder, then try again.",
    severity: "error",
  },
  repository_not_initialized: {
    failure_domain: "initialization",
    ownership: "primary",
    recovery_action: "initialize_repository",
    what_failed: "Repository initialization",
    why_failed: "CodeStrata configuration is not present in this repository.",
    next_step: "Initialize Repository, then run an assessment.",
    severity: "error",
  },
  initialization_failed: {
    failure_domain: "initialization",
    ownership: "primary",
    recovery_action: "initialize_repository",
    what_failed: "Repository initialization",
    why_failed: "Initialization did not complete successfully.",
    next_step: "Review CodeStrata output, then initialize again if needed.",
    severity: "error",
  },
  invalid_existing_configuration: {
    failure_domain: "initialization",
    ownership: "primary",
    recovery_action: "read_documentation",
    what_failed: "Repository configuration",
    why_failed: "Existing CodeStrata configuration is invalid and was not overwritten.",
    next_step: "Inspect the configuration, then follow documentation.",
    severity: "error",
  },
  partial_existing_configuration: {
    failure_domain: "initialization",
    ownership: "primary",
    recovery_action: "read_documentation",
    what_failed: "Repository configuration",
    why_failed: "Partial CodeStrata configuration was detected.",
    next_step: "Complete or repair configuration before assessing.",
    severity: "warning",
  },
  cli_unavailable: {
    failure_domain: "cli_discovery",
    ownership: "primary",
    recovery_action: "install_cli",
    what_failed: "CLI discovery",
    why_failed: "CodeStrata Engine CLI was not found.",
    next_step: "Install the CLI or correct the executable setting, then refresh.",
    severity: "error",
  },
  cli_incompatible: {
    failure_domain: "cli_discovery",
    ownership: "primary",
    recovery_action: "correct_cli_setting",
    what_failed: "CLI compatibility",
    why_failed: "The discovered CLI is not a compatible CodeStrata Engine.",
    next_step: "Install a supported Engine CLI or correct the executable setting.",
    severity: "error",
  },
  cli_probe_failed: {
    failure_domain: "cli_discovery",
    ownership: "primary",
    recovery_action: "install_cli",
    what_failed: "CLI probe",
    why_failed: "The extension could not verify the CodeStrata Engine CLI.",
    next_step: "Install or reconfigure the CLI, then try again.",
    severity: "error",
  },
  invalid_cli_configuration: {
    failure_domain: "cli_discovery",
    ownership: "primary",
    recovery_action: "correct_cli_setting",
    what_failed: "CLI configuration",
    why_failed: "The configured CLI path is invalid or unsafe.",
    next_step: "Correct the CodeStrata Engine executable setting.",
    severity: "error",
  },
  cli_invocation_failed: {
    failure_domain: "assessment",
    ownership: "primary",
    recovery_action: "run_assessment_again",
    what_failed: "Assessment invocation",
    why_failed: "The Engine CLI could not be started or completed abnormally.",
    next_step: "Confirm the CLI is installed, then run the assessment again.",
    severity: "error",
  },
  assessment_failed: {
    failure_domain: "assessment",
    ownership: "primary",
    recovery_action: "run_assessment_again",
    what_failed: "Engineering Assessment",
    why_failed: "The Engine assessment exited without success.",
    next_step: "Review CodeStrata output, then run the assessment again.",
    severity: "error",
  },
  assessment_cancelled: {
    failure_domain: "cancellation",
    ownership: "primary",
    recovery_action: "none",
    what_failed: "Assessment cancelled",
    why_failed: "The user cancelled the assessment.",
    next_step: "No recovery required. Run an assessment when ready.",
    severity: "info",
    primary_result_preserved: true,
  },
  report_not_found: {
    failure_domain: "report",
    ownership: "secondary",
    recovery_action: "run_assessment_again",
    what_failed: "Report availability",
    why_failed: "Assessment completed but the expected HTML report was not found.",
    next_step: "Run the assessment again, or open a report after a successful run.",
    severity: "warning",
    primary_result_preserved: true,
  },
  report_open_failed: {
    failure_domain: "report",
    ownership: "secondary",
    recovery_action: "open_report",
    what_failed: "Report opening",
    why_failed: "The local HTML report could not be opened.",
    next_step: "Try Open Report again, or open report.html from the Engine output folder.",
    severity: "warning",
    primary_result_preserved: true,
  },
  report_path_unsafe: {
    failure_domain: "report",
    ownership: "secondary",
    recovery_action: "run_assessment_again",
    what_failed: "Report path boundary",
    why_failed: "A report candidate was outside the allowed repository boundary.",
    next_step: "Run an assessment again so Engine writes a contained report.",
    severity: "warning",
    primary_result_preserved: true,
  },
  telemetry_isolated_failure: {
    failure_domain: "secondary_failure",
    ownership: "secondary",
    recovery_action: "none",
    what_failed: "Telemetry (isolated)",
    why_failed: "Telemetry failed independently of the primary operation.",
    next_step: "No recovery required for the primary result.",
    severity: "info",
    primary_result_preserved: true,
  },
  analytics_isolated_failure: {
    failure_domain: "secondary_failure",
    ownership: "secondary",
    recovery_action: "none",
    what_failed: "Analytics (isolated)",
    why_failed: "Analytics failed independently of the primary operation.",
    next_step: "No recovery required for the primary result.",
    severity: "info",
    primary_result_preserved: true,
  },
  progress_start_failed: {
    failure_domain: "progress",
    ownership: "secondary",
    recovery_action: "none",
    what_failed: "Progress UI",
    why_failed: "Progress presentation failed; primary assessment ownership is unchanged.",
    next_step: "Check CodeStrata output for the primary assessment result.",
    severity: "warning",
    primary_result_preserved: true,
  },
  user_declined: {
    failure_domain: "user_declined",
    ownership: "secondary",
    recovery_action: "none",
    what_failed: "User declined optional action",
    why_failed: "The user declined an optional follow-up action.",
    next_step: "No recovery required.",
    severity: "info",
    primary_result_preserved: true,
  },
  internal_workflow_error: {
    failure_domain: "internal",
    ownership: "primary",
    recovery_action: "read_documentation",
    what_failed: "Internal workflow",
    why_failed: "An unexpected extension workflow error occurred.",
    next_step: "Retry the command, or read documentation for support steps.",
    severity: "error",
  },
  invalid_transition: {
    failure_domain: "internal",
    ownership: "primary",
    recovery_action: "read_documentation",
    what_failed: "Workflow transition",
    why_failed: "An invalid workflow transition was attempted.",
    next_step: "Retry the command from a clean state.",
    severity: "error",
  },
};

const FALLBACK: CatalogEntry = {
  failure_domain: "internal",
  ownership: "primary",
  recovery_action: "read_documentation",
  what_failed: "Operation",
  why_failed: "The operation did not complete successfully.",
  next_step: "Review CodeStrata output, then retry or read documentation.",
  severity: "error",
};

function composeUserMessage(entry: CatalogEntry): string {
  return `${entry.what_failed}: ${entry.why_failed} Next: ${entry.next_step}`;
}

export function resolveRecoveryGuidance(
  failureCategory: string,
  options?: { readonly limitations?: readonly string[] }
): RecoveryGuidance {
  const entry = CATALOG[failureCategory] ?? {
    ...FALLBACK,
    what_failed: FALLBACK.what_failed,
  };
  const action = entry.recovery_action;
  const label =
    action === "none" ? undefined : RECOVERY_ACTION_LABELS[action];
  const commandId =
    action === "none" ? undefined : RECOVERY_ACTION_COMMANDS[action];
  return {
    failure_domain: entry.failure_domain,
    failure_category: CATALOG[failureCategory]
      ? failureCategory
      : "internal_workflow_error",
    ownership: entry.ownership,
    recovery_action: action,
    workflow_recovery_flag:
      action === "none" ? "none" : "user_action_available",
    what_failed: entry.what_failed,
    why_failed: entry.why_failed,
    next_step: entry.next_step,
    user_message: composeUserMessage(entry),
    action_label: label,
    command_id: commandId,
    auto_execute: false,
    primary_result_preserved: entry.primary_result_preserved ?? true,
    severity: entry.severity,
    limitations: [
      ...(options?.limitations ?? DEFAULT_RECOVERY_LIMITATIONS),
    ].sort(),
  };
}

export function knownFailureCategories(): readonly string[] {
  return Object.keys(CATALOG).sort();
}

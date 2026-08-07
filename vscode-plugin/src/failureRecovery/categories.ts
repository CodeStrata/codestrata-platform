/**
 * Bounded failure domains and recovery actions (Slice 13.8).
 */

export const FAILURE_DOMAINS = [
  "workspace",
  "initialization",
  "cli_discovery",
  "cli_installation",
  "assessment",
  "report",
  "progress",
  "cancellation",
  "user_declined",
  "internal",
  "secondary_failure",
] as const;

export type FailureDomain = (typeof FAILURE_DOMAINS)[number];

export const FAILURE_OWNERSHIPS = ["primary", "secondary"] as const;
export type FailureOwnership = (typeof FAILURE_OWNERSHIPS)[number];

/** Unified recovery actions (never auto-executed). */
export const RECOVERY_ACTIONS = [
  "initialize_repository",
  "install_cli",
  "correct_cli_setting",
  "run_assessment_again",
  "open_report",
  "select_workspace",
  "read_documentation",
  "none",
] as const;

export type RecoveryAction = (typeof RECOVERY_ACTIONS)[number];

/** Stable user-facing action labels (no paths). */
export const RECOVERY_ACTION_LABELS: Readonly<
  Record<Exclude<RecoveryAction, "none">, string>
> = {
  initialize_repository: "Initialize Repository",
  install_cli: "Install CLI",
  correct_cli_setting: "Correct CLI Setting",
  run_assessment_again: "Run Assessment Again",
  open_report: "Open Report",
  select_workspace: "Select Workspace",
  read_documentation: "Read Documentation",
};

/** Optional VS Code command ids for user-triggered actions. */
export const RECOVERY_ACTION_COMMANDS: Readonly<
  Partial<Record<RecoveryAction, string>>
> = {
  initialize_repository: "codestrata.init",
  install_cli: "codestrata.installEngine",
  correct_cli_setting: "codestrata.openDocumentation",
  run_assessment_again: "codestrata.assess",
  open_report: "codestrata.openHtmlReport",
  read_documentation: "codestrata.openDocumentation",
  // select_workspace: no command — user must open a folder
};

export const WORKFLOW_RECOVERY_FLAGS = [
  "none",
  "user_action_available",
] as const;

export type WorkflowRecoveryFlag =
  (typeof WORKFLOW_RECOVERY_FLAGS)[number];

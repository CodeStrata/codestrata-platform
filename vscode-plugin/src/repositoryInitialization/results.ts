/** Typed repository initialization results and errors (Slice 13.4). */

import { DEFAULT_REPO_INIT_LIMITATIONS } from "./policy";
import type { RepositoryInitState } from "./states";

export const REPO_INIT_RESULT_STATUSES = [
  "initialized",
  "already_initialized",
  "failed",
  "cancelled",
  "cli_unavailable",
  "workspace_unavailable",
  "invalid_existing_configuration",
  "partial_existing_configuration",
  "verification_failed",
] as const;

export type RepoInitResultStatus = (typeof REPO_INIT_RESULT_STATUSES)[number];

export const REPO_INIT_RECOVERY_CATEGORIES = [
  "install_cli",
  "correct_cli_setting",
  "inspect_existing_configuration",
  "retry_initialization",
  "select_workspace",
  "none",
] as const;

export type RepoInitRecoveryCategory =
  (typeof REPO_INIT_RECOVERY_CATEGORIES)[number];

export type RepositoryInitializationResult = {
  readonly status: RepoInitResultStatus;
  readonly prior_state: RepositoryInitState;
  readonly final_state: RepositoryInitState;
  readonly engine_invocation_count: number;
  readonly config_created: boolean;
  readonly existing_configuration_preserved: boolean;
  readonly post_init_verified: boolean;
  readonly assessment_invoked: false;
  readonly telemetry_invoked: false;
  readonly analytics_invoked: false;
  readonly report_opened: false;
  readonly recovery_category: RepoInitRecoveryCategory;
  readonly limitations: readonly string[];
};

export function repositoryInitializationResultToStableDict(
  result: RepositoryInitializationResult
): Record<string, unknown> {
  return {
    analytics_invoked: result.analytics_invoked,
    assessment_invoked: result.assessment_invoked,
    config_created: result.config_created,
    engine_invocation_count: result.engine_invocation_count,
    existing_configuration_preserved: result.existing_configuration_preserved,
    final_state: result.final_state,
    limitations: [...result.limitations].sort(),
    post_init_verified: result.post_init_verified,
    prior_state: result.prior_state,
    recovery_category: result.recovery_category,
    report_opened: result.report_opened,
    status: result.status,
    telemetry_invoked: result.telemetry_invoked,
  };
}

export function createRepoInitResult(
  partial: Omit<
    RepositoryInitializationResult,
    | "assessment_invoked"
    | "telemetry_invoked"
    | "analytics_invoked"
    | "report_opened"
    | "limitations"
  > & { readonly limitations?: readonly string[] }
): RepositoryInitializationResult {
  return {
    ...partial,
    assessment_invoked: false,
    telemetry_invoked: false,
    analytics_invoked: false,
    report_opened: false,
    limitations: [...(partial.limitations ?? DEFAULT_REPO_INIT_LIMITATIONS)].sort(),
  };
}

export const REPO_INIT_ERROR_CATEGORIES = [
  "workspace_unavailable",
  "cli_unavailable",
  "invalid_existing_configuration",
  "partial_existing_configuration",
  "initialization_failed",
  "initialization_cancelled",
  "post_init_verification_failed",
  "force_overwrite_forbidden",
  "initialization_internal_error",
] as const;

export type RepoInitErrorCategory = (typeof REPO_INIT_ERROR_CATEGORIES)[number];

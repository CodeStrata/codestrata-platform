/**
 * Repository initialization orchestration decisions (Slice 13.4).
 * Engine CLI remains the sole config writer; extension coordinates only.
 */

import {
  assertInitArgsForbidForce,
  detectRepositoryInitState,
} from "./detection";
import { DEFAULT_REPO_INIT_LIMITATIONS, REPO_INIT_POLICY_VERSION } from "./policy";
import {
  createRepoInitResult,
  type RepositoryInitializationResult,
  type RepoInitRecoveryCategory,
} from "./results";
import type { RepositoryInitState } from "./states";
import type { RepositoryInitializationDiagnostics } from "./diagnostics";

export type InitCliRunResult = {
  readonly exitCode: number;
  readonly cancelled: boolean;
};

export type InitPlan =
  | {
      readonly action: "skip_already_initialized";
      readonly prior_state: "initialized";
    }
  | {
      readonly action: "fail_invalid_existing";
      readonly prior_state: "invalid_configuration";
    }
  | {
      readonly action: "fail_partial_existing";
      readonly prior_state: "partial_initialization";
    }
  | {
      readonly action: "invoke_engine_init";
      readonly prior_state: RepositoryInitState;
    }
  | {
      readonly action: "fail_unknown_state";
      readonly prior_state: "unknown";
    };

export function planRepositoryInitialization(
  priorState: RepositoryInitState
): InitPlan {
  switch (priorState) {
    case "initialized":
      return { action: "skip_already_initialized", prior_state: "initialized" };
    case "invalid_configuration":
      return {
        action: "fail_invalid_existing",
        prior_state: "invalid_configuration",
      };
    case "partial_initialization":
      return {
        action: "fail_partial_existing",
        prior_state: "partial_initialization",
      };
    case "unknown":
      return { action: "fail_unknown_state", prior_state: "unknown" };
    case "not_initialized":
    default:
      return { action: "invoke_engine_init", prior_state: "not_initialized" };
  }
}

export function resultForPlanWithoutCli(
  plan: Exclude<InitPlan, { action: "invoke_engine_init" }>
): RepositoryInitializationResult {
  if (plan.action === "skip_already_initialized") {
    return createRepoInitResult({
      status: "already_initialized",
      prior_state: plan.prior_state,
      final_state: "initialized",
      engine_invocation_count: 0,
      config_created: false,
      existing_configuration_preserved: true,
      post_init_verified: true,
      recovery_category: "none",
    });
  }
  if (plan.action === "fail_invalid_existing") {
    return createRepoInitResult({
      status: "invalid_existing_configuration",
      prior_state: plan.prior_state,
      final_state: plan.prior_state,
      engine_invocation_count: 0,
      config_created: false,
      existing_configuration_preserved: true,
      post_init_verified: false,
      recovery_category: "inspect_existing_configuration",
    });
  }
  if (plan.action === "fail_partial_existing") {
    return createRepoInitResult({
      status: "partial_existing_configuration",
      prior_state: plan.prior_state,
      final_state: plan.prior_state,
      engine_invocation_count: 0,
      config_created: false,
      existing_configuration_preserved: true,
      post_init_verified: false,
      recovery_category: "inspect_existing_configuration",
    });
  }
  return createRepoInitResult({
    status: "failed",
    prior_state: plan.prior_state,
    final_state: plan.prior_state,
    engine_invocation_count: 0,
    config_created: false,
    existing_configuration_preserved: true,
    post_init_verified: false,
    recovery_category: "retry_initialization",
  });
}

export function resultAfterEngineInit(options: {
  readonly priorState: RepositoryInitState;
  readonly cli: InitCliRunResult;
  readonly finalState: RepositoryInitState;
}): RepositoryInitializationResult {
  if (options.cli.cancelled) {
    return createRepoInitResult({
      status: "cancelled",
      prior_state: options.priorState,
      final_state: options.finalState,
      engine_invocation_count: 1,
      config_created: false,
      existing_configuration_preserved: true,
      post_init_verified: false,
      recovery_category: "retry_initialization",
    });
  }
  if (options.cli.exitCode !== 0) {
    return createRepoInitResult({
      status: "failed",
      prior_state: options.priorState,
      final_state: options.finalState,
      engine_invocation_count: 1,
      config_created: false,
      existing_configuration_preserved: true,
      post_init_verified: false,
      recovery_category: "retry_initialization",
    });
  }
  if (options.finalState !== "initialized") {
    return createRepoInitResult({
      status: "verification_failed",
      prior_state: options.priorState,
      final_state: options.finalState,
      engine_invocation_count: 1,
      config_created: false,
      existing_configuration_preserved: true,
      post_init_verified: false,
      recovery_category: "retry_initialization",
    });
  }
  return createRepoInitResult({
    status: "initialized",
    prior_state: options.priorState,
    final_state: "initialized",
    engine_invocation_count: 1,
    config_created: true,
    existing_configuration_preserved: true,
    post_init_verified: true,
    recovery_category: "none",
  });
}

export function diagnosticsFromResult(
  result: RepositoryInitializationResult
): RepositoryInitializationDiagnostics {
  return {
    initialization_policy_version: REPO_INIT_POLICY_VERSION,
    prior_state: result.prior_state,
    terminal_status: result.status,
    engine_invocation_count: result.engine_invocation_count,
    config_created: result.config_created,
    existing_config_preserved: result.existing_configuration_preserved,
    post_init_verified: result.post_init_verified,
    cancelled: result.status === "cancelled",
    source_mutation_detected: false,
    telemetry_invoked: false,
    analytics_invoked: false,
    assessment_invoked: false,
    limitation_codes: result.limitations.length
      ? result.limitations
      : DEFAULT_REPO_INIT_LIMITATIONS,
  };
}

export function userMessageForInitResult(
  result: RepositoryInitializationResult
): string {
  switch (result.status) {
    case "initialized":
      return "CodeStrata configuration initialized.";
    case "already_initialized":
      return "Repository already initialized (existing configuration preserved).";
    case "invalid_existing_configuration":
      return "Existing CodeStrata configuration is invalid. It was not overwritten.";
    case "partial_existing_configuration":
      return "Partial CodeStrata configuration detected. It was not overwritten.";
    case "cli_unavailable":
      return "CodeStrata CLI unavailable. Initialization was not attempted.";
    case "workspace_unavailable":
      return "No eligible workspace folder for initialization.";
    case "cancelled":
      return "CodeStrata initialization cancelled.";
    case "verification_failed":
      return "Initialization reported success but configuration could not be verified.";
    case "failed":
    default:
      return "CodeStrata initialization failed. See output.";
  }
}

export function recoveryForDiscoveryFailure(): RepoInitRecoveryCategory {
  return "install_cli";
}

export {
  assertInitArgsForbidForce,
  detectRepositoryInitState,
};

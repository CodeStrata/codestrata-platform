/**
 * Assessment readiness and result orchestration (Slice 13.5).
 * Engine CLI remains assessment authority; extension coordinates only.
 */

import type { RepositoryInitState } from "../repositoryInitialization/states";
import {
  ASSESSMENT_EXECUTION_POLICY_VERSION,
  DEFAULT_ASSESSMENT_EXECUTION_LIMITATIONS,
} from "./policy";
import type { AssessmentExecutionDiagnostics } from "./diagnostics";
import {
  createAssessmentExecutionResult,
  type AssessmentConsentCategory,
  type AssessmentExecutionResult,
  type AssessmentRecoveryCategory,
} from "./results";

export type AssessmentOperation =
  | "run_assessment"
  | "run_assessment_with_ai";

export type AssessmentReadinessPlan =
  | {
      readonly action: "fail_workspace";
      readonly status: "workspace_unavailable";
      readonly recovery_category: "none";
    }
  | {
      readonly action: "fail_not_initialized";
      readonly status: "repository_not_initialized";
      readonly recovery_category: "initialize_repository";
    }
  | {
      readonly action: "fail_invalid_configuration";
      readonly status: "invalid_repository_configuration";
      readonly recovery_category: "inspect_configuration";
    }
  | {
      readonly action: "fail_partial_configuration";
      readonly status: "partial_repository_configuration";
      readonly recovery_category: "inspect_configuration";
    }
  | {
      readonly action: "fail_unknown_configuration";
      readonly status: "invalid_repository_configuration";
      readonly recovery_category: "inspect_configuration";
    }
  | {
      readonly action: "continue_to_cli_discovery";
    };

/**
 * Initialization gate before CLI discovery and before telemetry consent.
 */
export function planAssessmentReadiness(
  initState: RepositoryInitState
): AssessmentReadinessPlan {
  switch (initState) {
    case "initialized":
      return { action: "continue_to_cli_discovery" };
    case "not_initialized":
      return {
        action: "fail_not_initialized",
        status: "repository_not_initialized",
        recovery_category: "initialize_repository",
      };
    case "invalid_configuration":
      return {
        action: "fail_invalid_configuration",
        status: "invalid_repository_configuration",
        recovery_category: "inspect_configuration",
      };
    case "partial_initialization":
      return {
        action: "fail_partial_configuration",
        status: "partial_repository_configuration",
        recovery_category: "inspect_configuration",
      };
    case "unknown":
    default:
      return {
        action: "fail_unknown_configuration",
        status: "invalid_repository_configuration",
        recovery_category: "inspect_configuration",
      };
  }
}

export function resultForReadinessFailure(
  operation: AssessmentOperation,
  aiRequested: boolean,
  plan: Exclude<AssessmentReadinessPlan, { action: "continue_to_cli_discovery" }>
): AssessmentExecutionResult {
  return createAssessmentExecutionResult({
    operation,
    status: plan.status,
    ai_requested: aiRequested,
    primary_exit_category: "unavailable",
    product_invocation_count: 0,
    consent_category: "not_reached",
    report_expected: false,
    report_available: false,
    cancellation_category: "none",
    recovery_category: plan.recovery_category,
  });
}

export function resultForCliUnavailable(
  operation: AssessmentOperation,
  aiRequested: boolean,
  recovery: AssessmentRecoveryCategory = "install_cli"
): AssessmentExecutionResult {
  return createAssessmentExecutionResult({
    operation,
    status: "cli_unavailable",
    ai_requested: aiRequested,
    primary_exit_category: "unavailable",
    product_invocation_count: 0,
    consent_category: "not_reached",
    report_expected: false,
    report_available: false,
    cancellation_category: "none",
    recovery_category: recovery,
  });
}

export type AssessCliOutcome = {
  readonly exitCode: number;
  readonly cancelled: boolean;
  readonly reportAvailable: boolean;
};

/**
 * Map Engine CLI outcome to bounded result.
 * Finding counts / grades / AI advisor status never determine success.
 * Missing report after exit 0 is a distinct postcondition (not assessment failure).
 */
export function resultAfterEngineAssessment(options: {
  readonly operation: AssessmentOperation;
  readonly aiRequested: boolean;
  readonly consent: AssessmentConsentCategory;
  readonly cli: AssessCliOutcome;
}): AssessmentExecutionResult {
  if (options.cli.cancelled) {
    return createAssessmentExecutionResult({
      operation: options.operation,
      status: "cancelled",
      ai_requested: options.aiRequested,
      primary_exit_category: "cancelled",
      product_invocation_count: 1,
      consent_category: options.consent,
      report_expected: false,
      report_available: false,
      cancellation_category: "user_cancelled",
      recovery_category: "none",
    });
  }
  if (options.cli.exitCode !== 0) {
    return createAssessmentExecutionResult({
      operation: options.operation,
      status: "failure",
      ai_requested: options.aiRequested,
      primary_exit_category: "failure",
      product_invocation_count: 1,
      consent_category: options.consent,
      report_expected: false,
      report_available: false,
      cancellation_category: "none",
      recovery_category: "retry_assessment",
    });
  }
  if (!options.cli.reportAvailable) {
    return createAssessmentExecutionResult({
      operation: options.operation,
      status: "report_missing",
      ai_requested: options.aiRequested,
      primary_exit_category: "success",
      product_invocation_count: 1,
      consent_category: options.consent,
      report_expected: true,
      report_available: false,
      cancellation_category: "none",
      recovery_category: "open_report_manually",
    });
  }
  return createAssessmentExecutionResult({
    operation: options.operation,
    status: "success",
    ai_requested: options.aiRequested,
    primary_exit_category: "success",
    product_invocation_count: 1,
    consent_category: options.consent,
    report_expected: true,
    report_available: true,
    cancellation_category: "none",
    recovery_category: "none",
  });
}

export function diagnosticsFromAssessmentResult(
  result: AssessmentExecutionResult,
  readinessPassed: boolean
): AssessmentExecutionDiagnostics {
  return {
    assessment_policy_version: ASSESSMENT_EXECUTION_POLICY_VERSION,
    operation: result.operation,
    ai_requested: result.ai_requested,
    readiness_passed: readinessPassed,
    consent_category: result.consent_category,
    product_invocation_count: result.product_invocation_count,
    primary_exit_category: result.primary_exit_category,
    cancelled: result.status === "cancelled",
    report_expected: result.report_expected,
    report_available: result.report_available,
    telemetry_failure_isolated: true,
    analytics_failure_isolated: true,
    source_mutation_detected: false,
    configuration_mutation_detected: false,
    git_mutation_detected: false,
    terminal_status: result.status,
    limitation_codes: result.limitations.length
      ? result.limitations
      : DEFAULT_ASSESSMENT_EXECUTION_LIMITATIONS,
  };
}

export function userMessageForAssessmentReadiness(
  result: AssessmentExecutionResult
): string {
  switch (result.status) {
    case "repository_not_initialized":
      return "Repository is not initialized for CodeStrata. Run Initialize Repository first.";
    case "invalid_repository_configuration":
      return "Existing CodeStrata configuration is invalid. Assessment was not started.";
    case "partial_repository_configuration":
      return "Partial CodeStrata configuration detected. Assessment was not started.";
    case "cli_unavailable":
      return "CodeStrata CLI unavailable. Assessment was not started.";
    case "workspace_unavailable":
      return "No eligible workspace folder for assessment.";
    default:
      return "Assessment could not start.";
  }
}

export function mapInitStateToWorkflowFlag(
  state: RepositoryInitState
): "initialized" | "not_initialized" | "unknown" {
  if (state === "initialized") {
    return "initialized";
  }
  if (state === "not_initialized") {
    return "not_initialized";
  }
  return "unknown";
}

/** Assert assess args never include silent fallback / duplicate commands. */
export function assertSingleAssessInvocationArgs(
  args: readonly string[]
): void {
  const assessCount = args.filter((a) => a === "assess").length;
  if (assessCount !== 1) {
    throw new Error("duplicate_assess_invocation");
  }
  if (args.includes("init") || args.includes("doctor") || args.includes("scan")) {
    throw new Error("forbidden_fallback_command");
  }
  const withAi = args.includes("--with-ai");
  const noAi = args.includes("--no-ai");
  if (withAi && noAi) {
    throw new Error("conflicting_ai_flags");
  }
  if (!withAi && !noAi) {
    throw new Error("missing_ai_flag");
  }
}

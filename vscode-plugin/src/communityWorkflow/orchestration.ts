/**
 * Community workflow orchestration session (Slice 13.1).
 *
 * Tracks typed states, CLI invocation count, and progress lifecycle.
 * Does not spawn the Engine CLI itself — callers remain authoritative.
 */

import type { TelemetryDecisionCategory } from "./context";
import { createWorkflowContext, type WorkflowContext } from "./context";
import type { WorkflowErrorCategory } from "./errors";
import type { WorkflowOperation } from "./operations";
import { DEFAULT_WORKFLOW_LIMITATIONS, WORKFLOW_POLICY_VERSION } from "./policy";
import type {
  CommunityWorkflowResult,
  PrimaryExitCategory,
  WorkflowResultStatus,
} from "./results";
import type { WorkflowState } from "./states";
import { assertTransition } from "./transitions";
import type { WorkflowDiagnostics } from "./diagnostics";
import { workflowDiagnosticsToStableDict } from "./diagnostics";

export type WorkflowSessionOptions = {
  readonly operation: WorkflowOperation;
  readonly aiRequested?: boolean;
  readonly cancellationSupported?: boolean;
  readonly workspaceAvailable?: boolean;
  readonly workspaceKind?: WorkflowContext["workspace_kind"];
  readonly repositoryInitialized?: WorkflowContext["repository_initialized"];
  readonly limitations?: readonly string[];
};

export class CommunityWorkflowSession {
  private state: WorkflowState = "idle";
  private transitionCount = 0;
  private cliInvocationCount = 0;
  private discoveryProbeCount = 0;
  private discoveryStatus = "not_attempted";
  private progressStarted = false;
  private progressClosed = false;
  private reportAvailable = false;
  private reportOpened = false;
  private telemetryDecision: TelemetryDecisionCategory = "not_applicable";
  private telemetryFailureIsolated = true;
  private analyticsFailureIsolated = true;
  private primaryResultPreserved = true;
  private terminalStatus: WorkflowResultStatus | "in_progress" = "in_progress";
  private resultCategory: WorkflowErrorCategory | "ok" = "ok";
  private primaryExit: PrimaryExitCategory = "not_run";
  private recoveryCategory: "none" | "user_action_available" = "none";
  private readonly operation: WorkflowOperation;
  private readonly aiRequested: boolean;
  private readonly cancellationSupported: boolean;
  private readonly workspaceAvailable: boolean;
  private readonly workspaceKind: WorkflowContext["workspace_kind"];
  private readonly repositoryInitialized: WorkflowContext["repository_initialized"];
  private readonly limitations: readonly string[];

  constructor(options: WorkflowSessionOptions) {
    this.operation = options.operation;
    this.aiRequested = options.aiRequested ?? false;
    this.cancellationSupported = options.cancellationSupported ?? true;
    this.workspaceAvailable = options.workspaceAvailable ?? true;
    this.workspaceKind = options.workspaceKind ?? "folder_workspace";
    this.repositoryInitialized = options.repositoryInitialized ?? "unknown";
    this.limitations = [...(options.limitations ?? DEFAULT_WORKFLOW_LIMITATIONS)].sort();
  }

  getCurrentState(): WorkflowState {
    return this.state;
  }

  getCliInvocationCount(): number {
    return this.cliInvocationCount;
  }

  getDiscoveryProbeCount(): number {
    return this.discoveryProbeCount;
  }

  getDiscoveryStatus(): string {
    return this.discoveryStatus;
  }

  context(): WorkflowContext {
    return createWorkflowContext({
      operation: this.operation,
      workspace_available: this.workspaceAvailable,
      workspace_kind: this.workspaceKind,
      repository_initialized: this.repositoryInitialized,
      ai_requested: this.aiRequested,
      telemetry_decision: this.telemetryDecision,
      output_mode: "notification_progress",
      cancellation_supported: this.cancellationSupported,
    });
  }

  transitionTo(next: WorkflowState): void {
    assertTransition(this.state, next);
    this.state = next;
    this.transitionCount += 1;
  }

  /** Record exactly one product CLI process (init/assess) for this operation. */
  recordCliInvocation(): void {
    this.cliInvocationCount += 1;
  }

  /** Record a side-effect-free discovery/version probe (not a product invocation). */
  recordDiscoveryProbe(): void {
    this.discoveryProbeCount += 1;
  }

  setDiscoveryStatus(status: string): void {
    this.discoveryStatus = status;
  }

  markProgressStarted(): void {
    this.progressStarted = true;
  }

  markProgressClosed(): void {
    this.progressClosed = true;
  }

  setTelemetryDecision(decision: TelemetryDecisionCategory): void {
    this.telemetryDecision = decision;
  }

  setReportAvailable(available: boolean): void {
    this.reportAvailable = available;
  }

  setReportOpened(opened: boolean): void {
    this.reportOpened = opened;
  }

  markTelemetryIsolatedFailure(): void {
    this.telemetryFailureIsolated = true;
  }

  markAnalyticsIsolatedFailure(): void {
    this.analyticsFailureIsolated = true;
  }

  /**
   * Complete the session with a primary CLI/user outcome.
   * Report-open failure must not rewrite a successful assessment.
   */
  complete(options: {
    readonly status: WorkflowResultStatus;
    readonly resultCategory?: WorkflowErrorCategory | "ok";
    readonly primaryExit: PrimaryExitCategory;
    readonly reportOpenFailed?: boolean;
    /** Slice 13.8: set when recovery guidance offers a user action. */
    readonly recoveryCategory?: "none" | "user_action_available";
  }): CommunityWorkflowResult {
    if (options.status === "success") {
      this.transitionTo("completed");
    } else if (options.status === "cancelled") {
      this.transitionTo("cancelled");
    } else if (this.state !== "failed" && this.state !== "cancelled" && this.state !== "completed") {
      this.transitionTo("failed");
    }
    this.terminalStatus = options.status;
    this.primaryExit = options.primaryExit;
    if (options.reportOpenFailed && options.primaryExit === "success") {
      // Distinct post-processing: assessment success preserved.
      this.resultCategory = "report_open_failed";
      this.primaryResultPreserved = true;
    } else {
      this.resultCategory = options.resultCategory ?? (options.status === "success" ? "ok" : "assessment_failed");
      this.primaryResultPreserved = true;
    }
    this.recoveryCategory = options.recoveryCategory ?? "none";
    if (!this.progressClosed && this.progressStarted) {
      this.progressClosed = true;
    }
    return this.toResult();
  }

  toResult(): CommunityWorkflowResult {
    return {
      operation: this.operation,
      status:
        this.terminalStatus === "in_progress" ? "failure" : this.terminalStatus,
      result_category: this.resultCategory,
      report_available: this.reportAvailable,
      report_opened: this.reportOpened,
      ai_requested: this.aiRequested,
      telemetry_decision_category: this.telemetryDecision,
      primary_exit_category: this.primaryExit,
      recovery_category: this.recoveryCategory,
      limitations: this.limitations,
    };
  }

  diagnostics(): WorkflowDiagnostics {
    return {
      workflow_policy_version: WORKFLOW_POLICY_VERSION,
      operation: this.operation,
      current_state: this.state,
      terminal_status: this.terminalStatus,
      transition_count: this.transitionCount,
      cli_invocation_count: this.cliInvocationCount,
      discovery_probe_count: this.discoveryProbeCount,
      discovery_status: this.discoveryStatus,
      progress_started: this.progressStarted,
      progress_closed: this.progressClosed,
      report_available: this.reportAvailable,
      report_opened: this.reportOpened,
      telemetry_decision_category: this.telemetryDecision,
      telemetry_failure_isolated: this.telemetryFailureIsolated,
      analytics_failure_isolated: this.analyticsFailureIsolated,
      primary_result_preserved: this.primaryResultPreserved,
      limitation_codes: this.limitations,
    };
  }

  diagnosticsStable(): Record<string, unknown> {
    return workflowDiagnosticsToStableDict(this.diagnostics());
  }
}

export function mapConsentToDecisionCategory(input: {
  readonly decision: string;
  readonly prompted: boolean;
  readonly interactive: boolean;
}): TelemetryDecisionCategory {
  if (input.decision === "allowed_for_session") {
    return "allowed_for_session";
  }
  if (
    input.decision === "non_interactive_disabled" ||
    (!input.interactive && !input.prompted)
  ) {
    return "suppressed_non_interactive";
  }
  return "denied";
}

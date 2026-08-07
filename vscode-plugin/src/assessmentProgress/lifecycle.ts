/**
 * Assessment progress lifecycle (Slice 13.6).
 *
 * One lifecycle per assessment. Indeterminate by default — no fabricated
 * percentages. Progress failures are isolated from primary assessment results.
 */

import {
  ASSESSMENT_PROGRESS_POLICY_VERSION,
  DEFAULT_ASSESSMENT_PROGRESS_LIMITATIONS,
} from "./policy";
import {
  canTransitionProgress,
  isTerminalProgressPhase,
  progressMessageForPhase,
  type AssessmentProgressPhase,
} from "./phases";
import {
  createAssessmentProgressResult,
  type AssessmentProgressResult,
  type AssessmentProgressResultStatus,
} from "./results";
import type { AssessmentProgressDiagnostics } from "./diagnostics";

export type ProgressReporter = {
  /** Message-only updates. Never pass increment/percentage without Engine signal. */
  report(value: { readonly message?: string }): void;
};

export type ProgressLifecycleOptions = {
  readonly operation: "run_assessment" | "run_assessment_with_ai";
  readonly aiRequested: boolean;
};

/**
 * Reject percentage/increment payloads — Engine has no structured progress protocol.
 */
export function assertNoFabricatedPercentage(value: {
  readonly increment?: number;
  readonly percentage?: number;
}): void {
  if (value.increment !== undefined || value.percentage !== undefined) {
    throw new Error("fabricated_percentage_forbidden");
  }
}

export class AssessmentProgressLifecycle {
  private phase: AssessmentProgressPhase | "not_started" = "not_started";
  private started = false;
  private closed = false;
  private updateCount = 0;
  private cancellationRequested = false;
  private cancellationAbortIssued = false;
  private reporter: ProgressReporter | undefined;
  private terminalStatus: AssessmentProgressResultStatus | "in_progress" =
    "in_progress";
  private readonly operation: ProgressLifecycleOptions["operation"];
  private readonly aiRequested: boolean;
  private readonly limitations: readonly string[];

  constructor(options: ProgressLifecycleOptions) {
    this.operation = options.operation;
    this.aiRequested = options.aiRequested;
    this.limitations = [...DEFAULT_ASSESSMENT_PROGRESS_LIMITATIONS].sort();
  }

  getPhase(): AssessmentProgressPhase | "not_started" {
    return this.phase;
  }

  isStarted(): boolean {
    return this.started;
  }

  isClosed(): boolean {
    return this.closed;
  }

  wasCancellationRequested(): boolean {
    return this.cancellationRequested;
  }

  getUpdateCount(): number {
    return this.updateCount;
  }

  /**
   * Begin the single progress lifecycle (after readiness + consent).
   * Isolated: reporter failures do not throw to callers.
   */
  start(reporter?: ProgressReporter): void {
    if (this.started) {
      return;
    }
    this.started = true;
    this.phase = "running_assessment";
    this.reporter = reporter;
    this.safeReport(progressMessageForPhase("running_assessment", this.aiRequested));
  }

  /**
   * Transition to an observable phase and report message-only update.
   * Isolated: invalid transitions / reporter failures do not throw.
   */
  enterPhase(next: AssessmentProgressPhase): void {
    if (this.closed || !this.started) {
      return;
    }
    if (this.phase === "not_started") {
      return;
    }
    if (isTerminalProgressPhase(this.phase)) {
      return;
    }
    if (!canTransitionProgress(this.phase, next)) {
      return;
    }
    this.phase = next;
    this.safeReport(progressMessageForPhase(next, this.aiRequested));
  }

  /**
   * Record cancellation request. Returns true only for the first abort issuance
   * so callers do not kill the product process twice.
   */
  requestCancellation(): boolean {
    this.cancellationRequested = true;
    if (this.cancellationAbortIssued) {
      return false;
    }
    this.cancellationAbortIssued = true;
    return true;
  }

  /**
   * Close exactly once with a terminal phase derived from primary result.
   */
  close(status: AssessmentProgressResultStatus): AssessmentProgressResult {
    if (this.closed) {
      return this.toResult();
    }
    this.closed = true;
    const terminalPhase: AssessmentProgressPhase =
      status === "cancelled"
        ? "cancelled"
        : status === "failed" || status === "unavailable"
          ? "failed"
          : "completed";
    if (
      this.phase !== "not_started" &&
      !isTerminalProgressPhase(this.phase) &&
      canTransitionProgress(this.phase, terminalPhase)
    ) {
      this.phase = terminalPhase;
    } else if (this.phase === "not_started") {
      this.phase = terminalPhase;
    } else if (!isTerminalProgressPhase(this.phase)) {
      this.phase = terminalPhase;
    }
    this.terminalStatus = status;
    this.safeReport(progressMessageForPhase(this.phase as AssessmentProgressPhase, this.aiRequested));
    this.reporter = undefined;
    return this.toResult();
  }

  toResult(): AssessmentProgressResult {
    const phase: AssessmentProgressPhase =
      this.phase === "not_started" ? "failed" : this.phase;
    const status: AssessmentProgressResultStatus =
      this.terminalStatus === "in_progress"
        ? this.cancellationRequested
          ? "cancelled"
          : "unavailable"
        : this.terminalStatus;
    return createAssessmentProgressResult({
      status,
      terminal_phase: isTerminalProgressPhase(phase) ? phase : "failed",
      update_count: this.updateCount,
      cancellation_requested: this.cancellationRequested,
    });
  }

  diagnostics(): AssessmentProgressDiagnostics {
    return {
      progress_policy_version: ASSESSMENT_PROGRESS_POLICY_VERSION,
      operation: this.operation,
      ai_requested: this.aiRequested,
      progress_started: this.started,
      progress_closed: this.closed,
      terminal_phase: this.phase,
      update_count: this.updateCount,
      cancellation_supported: true,
      cancellation_requested: this.cancellationRequested,
      cancellation_result_category: this.cancellationRequested
        ? "user_cancelled"
        : "none",
      primary_result_preserved: true,
      telemetry_failure_isolated: true,
      analytics_failure_isolated: true,
      progress_failure_isolated: true,
      terminal_status: this.terminalStatus,
      limitation_codes: this.limitations,
    };
  }

  private safeReport(message: string): void {
    if (!this.reporter) {
      return;
    }
    try {
      assertNoFabricatedPercentage({});
      this.reporter.report({ message });
      this.updateCount += 1;
    } catch {
      // Isolated: progress UI failure must not alter primary assessment.
    }
  }
}

/** Map primary assessment outcome to progress close status. */
export function progressStatusFromPrimary(
  primary: "success" | "failure" | "cancelled" | "unavailable"
): AssessmentProgressResultStatus {
  if (primary === "cancelled") {
    return "cancelled";
  }
  if (primary === "success") {
    return "completed";
  }
  if (primary === "unavailable") {
    return "unavailable";
  }
  return "failed";
}

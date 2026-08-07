/** CodeStrata assessment-progress contract (Slice 13.6). */

export {
  ASSESSMENT_PROGRESS_POLICY_ID,
  ASSESSMENT_PROGRESS_POLICY_VERSION,
  DEFAULT_ASSESSMENT_PROGRESS_LIMITATIONS,
  createAssessmentProgressPolicy,
  assessmentProgressPolicyToStableDict,
  type AssessmentProgressPolicy,
} from "./policy";

export {
  ASSESSMENT_PROGRESS_PHASES,
  TERMINAL_PROGRESS_PHASES,
  ALLOWED_PROGRESS_TRANSITIONS,
  isAssessmentProgressPhase,
  isTerminalProgressPhase,
  canTransitionProgress,
  progressMessageForPhase,
  progressTitle,
  type AssessmentProgressPhase,
} from "./phases";

export {
  ASSESSMENT_PROGRESS_RESULT_STATUSES,
  ASSESSMENT_PROGRESS_ERROR_CATEGORIES,
  createAssessmentProgressResult,
  assessmentProgressResultToStableDict,
  type AssessmentProgressResultStatus,
  type AssessmentProgressResult,
  type AssessmentProgressErrorCategory,
} from "./results";

export {
  assessmentProgressDiagnosticsToStableDict,
  progressDiagnosticsContainForbiddenKeys,
  type AssessmentProgressDiagnostics,
} from "./diagnostics";

export {
  AssessmentProgressLifecycle,
  assertNoFabricatedPercentage,
  progressStatusFromPrimary,
  type ProgressReporter,
  type ProgressLifecycleOptions,
} from "./lifecycle";

/** CodeStrata assessment-execution contract (Slice 13.5). */

export {
  ASSESSMENT_EXECUTION_POLICY_ID,
  ASSESSMENT_EXECUTION_POLICY_VERSION,
  DEFAULT_ASSESSMENT_EXECUTION_LIMITATIONS,
  createAssessmentExecutionPolicy,
  assessmentExecutionPolicyToStableDict,
  type AssessmentExecutionPolicy,
} from "./policy";

export {
  ASSESSMENT_EXECUTION_RESULT_STATUSES,
  ASSESSMENT_PRIMARY_EXIT_CATEGORIES,
  ASSESSMENT_RECOVERY_CATEGORIES,
  ASSESSMENT_CONSENT_CATEGORIES,
  ASSESSMENT_ERROR_CATEGORIES,
  createAssessmentExecutionResult,
  assessmentExecutionResultToStableDict,
  type AssessmentExecutionResultStatus,
  type AssessmentPrimaryExitCategory,
  type AssessmentRecoveryCategory,
  type AssessmentConsentCategory,
  type AssessmentExecutionResult,
  type AssessmentErrorCategory,
} from "./results";

export {
  assessmentExecutionDiagnosticsToStableDict,
  assessmentDiagnosticsContainForbiddenKeys,
  type AssessmentExecutionDiagnostics,
} from "./diagnostics";

export {
  planAssessmentReadiness,
  resultForReadinessFailure,
  resultForCliUnavailable,
  resultAfterEngineAssessment,
  diagnosticsFromAssessmentResult,
  userMessageForAssessmentReadiness,
  mapInitStateToWorkflowFlag,
  assertSingleAssessInvocationArgs,
  type AssessmentOperation,
  type AssessmentReadinessPlan,
  type AssessCliOutcome,
} from "./orchestration";

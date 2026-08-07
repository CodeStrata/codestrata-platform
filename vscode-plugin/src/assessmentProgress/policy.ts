/**
 * Community VS Code assessment-progress policy (Slice 13.6).
 * policy_id = community-vscode-assessment-progress-policy
 * policy_version = 1.0
 */

export const ASSESSMENT_PROGRESS_POLICY_ID =
  "community-vscode-assessment-progress-policy" as const;
export const ASSESSMENT_PROGRESS_POLICY_VERSION = "1.0" as const;

export type AssessmentProgressPolicy = {
  readonly policy_id: typeof ASSESSMENT_PROGRESS_POLICY_ID;
  readonly policy_version: typeof ASSESSMENT_PROGRESS_POLICY_VERSION;
  readonly one_progress_lifecycle_per_assessment: true;
  readonly progress_starts_after_readiness: true;
  readonly progress_starts_after_consent: true;
  readonly progress_is_indeterminate_by_default: true;
  readonly fabricated_percentage_allowed: false;
  readonly trustworthy_engine_signal_required_for_percentage: true;
  readonly cancellation_supported: true;
  readonly cancellation_causes_retry: false;
  readonly primary_result_authoritative: true;
  readonly progress_failure_isolated: true;
  readonly telemetry_failure_isolated: true;
  readonly analytics_failure_isolated: true;
  readonly source_data_allowed: false;
  readonly repository_identity_allowed: false;
  readonly provider_model_allowed: false;
  readonly engine_structured_progress_available: false;
  readonly limitations: readonly string[];
};

export const DEFAULT_ASSESSMENT_PROGRESS_LIMITATIONS: readonly string[] = [
  "indeterminate_progress_only",
  "no_engine_structured_progress_protocol",
  "process_cancellation_mechanism_retained",
  "report_opening_complete_via_13_7",
  "recovery_framework_available_via_13_8",
  "no_full_extension_host_ui_automation",
  "worktree_uncommitted",
] as const;

export function createAssessmentProgressPolicy(
  limitations: readonly string[] = DEFAULT_ASSESSMENT_PROGRESS_LIMITATIONS
): AssessmentProgressPolicy {
  return {
    policy_id: ASSESSMENT_PROGRESS_POLICY_ID,
    policy_version: ASSESSMENT_PROGRESS_POLICY_VERSION,
    one_progress_lifecycle_per_assessment: true,
    progress_starts_after_readiness: true,
    progress_starts_after_consent: true,
    progress_is_indeterminate_by_default: true,
    fabricated_percentage_allowed: false,
    trustworthy_engine_signal_required_for_percentage: true,
    cancellation_supported: true,
    cancellation_causes_retry: false,
    primary_result_authoritative: true,
    progress_failure_isolated: true,
    telemetry_failure_isolated: true,
    analytics_failure_isolated: true,
    source_data_allowed: false,
    repository_identity_allowed: false,
    provider_model_allowed: false,
    engine_structured_progress_available: false,
    limitations: [...limitations].sort(),
  };
}

export function assessmentProgressPolicyToStableDict(
  policy: AssessmentProgressPolicy
): Record<string, unknown> {
  return {
    analytics_failure_isolated: policy.analytics_failure_isolated,
    cancellation_causes_retry: policy.cancellation_causes_retry,
    cancellation_supported: policy.cancellation_supported,
    engine_structured_progress_available:
      policy.engine_structured_progress_available,
    fabricated_percentage_allowed: policy.fabricated_percentage_allowed,
    limitations: [...policy.limitations].sort(),
    one_progress_lifecycle_per_assessment:
      policy.one_progress_lifecycle_per_assessment,
    policy_id: policy.policy_id,
    policy_version: policy.policy_version,
    primary_result_authoritative: policy.primary_result_authoritative,
    progress_failure_isolated: policy.progress_failure_isolated,
    progress_is_indeterminate_by_default:
      policy.progress_is_indeterminate_by_default,
    progress_starts_after_consent: policy.progress_starts_after_consent,
    progress_starts_after_readiness: policy.progress_starts_after_readiness,
    provider_model_allowed: policy.provider_model_allowed,
    repository_identity_allowed: policy.repository_identity_allowed,
    source_data_allowed: policy.source_data_allowed,
    telemetry_failure_isolated: policy.telemetry_failure_isolated,
    trustworthy_engine_signal_required_for_percentage:
      policy.trustworthy_engine_signal_required_for_percentage,
  };
}

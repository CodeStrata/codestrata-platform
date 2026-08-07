/**
 * Community VS Code HTML report-opening policy (Slice 13.7).
 * policy_id = community-vscode-report-opening-policy
 * policy_version = 1.0
 */

export const REPORT_OPENING_POLICY_ID =
  "community-vscode-report-opening-policy" as const;
export const REPORT_OPENING_POLICY_VERSION = "1.0" as const;

/** Fixed Engine HTML report basename (not repository-specific). */
export const ENGINE_HTML_REPORT_BASENAME = "report.html" as const;

export type ReportOpeningPolicy = {
  readonly policy_id: typeof REPORT_OPENING_POLICY_ID;
  readonly policy_version: typeof REPORT_OPENING_POLICY_VERSION;
  readonly engine_report_authoritative: true;
  readonly local_only: true;
  readonly html_only: true;
  readonly filesystem_crawl_allowed: false;
  readonly repository_containment_required: true;
  readonly output_boundary_containment_required: true;
  readonly remote_uri_allowed: false;
  readonly symlink_escape_allowed: false;
  readonly report_content_parsing_allowed: false;
  readonly report_content_transmission_allowed: false;
  /** Approach B: prompt user; do not auto-open without explicit action. */
  readonly automatic_open_after_success: false;
  readonly automatic_open_after_failure: false;
  readonly automatic_open_after_cancel: false;
  readonly primary_result_authoritative: true;
  readonly report_open_failure_isolated: true;
  readonly telemetry_allowed: false;
  readonly analytics_allowed: false;
  readonly limitations: readonly string[];
};

export const DEFAULT_REPORT_OPENING_LIMITATIONS: readonly string[] = [
  "prompt_driven_open_retained",
  "stale_certainty_limited_to_engine_run_directory",
  "symlink_junction_partially_mock_validated",
  "system_browser_not_launched_in_tests",
  "recovery_framework_available_via_13_8",
  "no_full_extension_host_ui_automation",
  "worktree_uncommitted",
] as const;

export function createReportOpeningPolicy(
  limitations: readonly string[] = DEFAULT_REPORT_OPENING_LIMITATIONS
): ReportOpeningPolicy {
  return {
    policy_id: REPORT_OPENING_POLICY_ID,
    policy_version: REPORT_OPENING_POLICY_VERSION,
    engine_report_authoritative: true,
    local_only: true,
    html_only: true,
    filesystem_crawl_allowed: false,
    repository_containment_required: true,
    output_boundary_containment_required: true,
    remote_uri_allowed: false,
    symlink_escape_allowed: false,
    report_content_parsing_allowed: false,
    report_content_transmission_allowed: false,
    automatic_open_after_success: false,
    automatic_open_after_failure: false,
    automatic_open_after_cancel: false,
    primary_result_authoritative: true,
    report_open_failure_isolated: true,
    telemetry_allowed: false,
    analytics_allowed: false,
    limitations: [...limitations].sort(),
  };
}

export function reportOpeningPolicyToStableDict(
  policy: ReportOpeningPolicy
): Record<string, unknown> {
  return {
    analytics_allowed: policy.analytics_allowed,
    automatic_open_after_cancel: policy.automatic_open_after_cancel,
    automatic_open_after_failure: policy.automatic_open_after_failure,
    automatic_open_after_success: policy.automatic_open_after_success,
    engine_report_authoritative: policy.engine_report_authoritative,
    filesystem_crawl_allowed: policy.filesystem_crawl_allowed,
    html_only: policy.html_only,
    limitations: [...policy.limitations].sort(),
    local_only: policy.local_only,
    output_boundary_containment_required:
      policy.output_boundary_containment_required,
    policy_id: policy.policy_id,
    policy_version: policy.policy_version,
    primary_result_authoritative: policy.primary_result_authoritative,
    remote_uri_allowed: policy.remote_uri_allowed,
    report_content_parsing_allowed: policy.report_content_parsing_allowed,
    report_content_transmission_allowed:
      policy.report_content_transmission_allowed,
    report_open_failure_isolated: policy.report_open_failure_isolated,
    repository_containment_required: policy.repository_containment_required,
    symlink_escape_allowed: policy.symlink_escape_allowed,
    telemetry_allowed: policy.telemetry_allowed,
  };
}

/**
 * Community VS Code source-locality policy (Slice 13.10).
 * policy_id = community-vscode-source-locality-policy
 * policy_version = 1.0
 */

export const SOURCE_LOCALITY_POLICY_ID =
  "community-vscode-source-locality-policy" as const;
export const SOURCE_LOCALITY_POLICY_VERSION = "1.0" as const;

export type SourceLocalityPolicy = {
  readonly policy_id: typeof SOURCE_LOCALITY_POLICY_ID;
  readonly policy_version: typeof SOURCE_LOCALITY_POLICY_VERSION;
  readonly extension_source_upload_allowed: false;
  readonly extension_source_packaging_allowed: false;
  readonly extension_source_network_transmission_allowed: false;
  readonly extension_report_upload_allowed: false;
  readonly extension_report_network_transmission_allowed: false;
  readonly extension_telemetry_source_fields_allowed: false;
  readonly extension_analytics_source_fields_allowed: false;
  readonly extension_cloud_api_access_allowed: false;
  readonly extension_data_lake_access_allowed: false;
  readonly extension_ai_provider_calls_allowed: false;
  readonly engine_cli_local_process_authoritative: true;
  readonly standard_assessment_extension_network_allowed: false;
  readonly ai_assessment_engine_provider_flow_possible: true;
  readonly provider_credentials_extension_owned: false;
  readonly source_file_mutation_allowed: false;
  readonly git_mutation_allowed: false;
  readonly local_generated_artifacts_allowed: true;
  readonly limitations: readonly string[];
};

export const DEFAULT_SOURCE_LOCALITY_LIMITATIONS: readonly string[] = [
  "ai_enabled_engine_may_use_external_configured_provider",
  "report_browser_behavior_outside_extension_not_fully_controlled",
  "static_network_dependency_verification_partly_source_based",
  "no_full_extension_host_ui_automation",
  "cli_compatibility_matrix_active_via_13_11",
  "marketplace_complete_via_13_12_13_13",
  "worktree_uncommitted",
] as const;

export function createSourceLocalityPolicy(
  limitations: readonly string[] = DEFAULT_SOURCE_LOCALITY_LIMITATIONS
): SourceLocalityPolicy {
  return {
    policy_id: SOURCE_LOCALITY_POLICY_ID,
    policy_version: SOURCE_LOCALITY_POLICY_VERSION,
    extension_source_upload_allowed: false,
    extension_source_packaging_allowed: false,
    extension_source_network_transmission_allowed: false,
    extension_report_upload_allowed: false,
    extension_report_network_transmission_allowed: false,
    extension_telemetry_source_fields_allowed: false,
    extension_analytics_source_fields_allowed: false,
    extension_cloud_api_access_allowed: false,
    extension_data_lake_access_allowed: false,
    extension_ai_provider_calls_allowed: false,
    engine_cli_local_process_authoritative: true,
    standard_assessment_extension_network_allowed: false,
    ai_assessment_engine_provider_flow_possible: true,
    provider_credentials_extension_owned: false,
    source_file_mutation_allowed: false,
    git_mutation_allowed: false,
    local_generated_artifacts_allowed: true,
    limitations: [...limitations].sort(),
  };
}

export function sourceLocalityPolicyToStableDict(
  policy: SourceLocalityPolicy
): Record<string, unknown> {
  return {
    ai_assessment_engine_provider_flow_possible:
      policy.ai_assessment_engine_provider_flow_possible,
    engine_cli_local_process_authoritative:
      policy.engine_cli_local_process_authoritative,
    extension_ai_provider_calls_allowed:
      policy.extension_ai_provider_calls_allowed,
    extension_analytics_source_fields_allowed:
      policy.extension_analytics_source_fields_allowed,
    extension_cloud_api_access_allowed:
      policy.extension_cloud_api_access_allowed,
    extension_data_lake_access_allowed:
      policy.extension_data_lake_access_allowed,
    extension_report_network_transmission_allowed:
      policy.extension_report_network_transmission_allowed,
    extension_report_upload_allowed: policy.extension_report_upload_allowed,
    extension_source_network_transmission_allowed:
      policy.extension_source_network_transmission_allowed,
    extension_source_packaging_allowed:
      policy.extension_source_packaging_allowed,
    extension_source_upload_allowed: policy.extension_source_upload_allowed,
    extension_telemetry_source_fields_allowed:
      policy.extension_telemetry_source_fields_allowed,
    git_mutation_allowed: policy.git_mutation_allowed,
    limitations: [...policy.limitations].sort(),
    local_generated_artifacts_allowed:
      policy.local_generated_artifacts_allowed,
    policy_id: policy.policy_id,
    policy_version: policy.policy_version,
    provider_credentials_extension_owned:
      policy.provider_credentials_extension_owned,
    source_file_mutation_allowed: policy.source_file_mutation_allowed,
    standard_assessment_extension_network_allowed:
      policy.standard_assessment_extension_network_allowed,
  };
}

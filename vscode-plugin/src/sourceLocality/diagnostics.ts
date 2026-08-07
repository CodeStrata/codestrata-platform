/** Privacy-safe source-locality diagnostics (Slice 13.10). */

import { SOURCE_LOCALITY_POLICY_VERSION } from "./policy";

export type SourceLocalityDiagnostics = {
  readonly locality_policy_version: typeof SOURCE_LOCALITY_POLICY_VERSION;
  readonly operation: string;
  readonly extension_source_upload: false;
  readonly extension_source_network: false;
  readonly telemetry_source_fields: false;
  readonly analytics_source_fields: false;
  readonly cloud_client_used: false;
  readonly data_lake_client_used: false;
  readonly extension_ai_client_used: false;
  readonly engine_ai_provider_boundary:
    | "not_applicable"
    | "engine_owned_when_configured";
  readonly source_mutation_detected: false;
  readonly git_mutation_detected: false;
  readonly identity_used: false;
  readonly provider_credentials_extension_owned: false;
  readonly limitations: readonly string[];
};

const FORBIDDEN_KEYS = [
  "path",
  "uri",
  "workspace",
  "stdout",
  "stderr",
  "source",
  "html",
  "url",
  "credential",
  "password",
  "token",
  "api_key",
  "machineId",
  "installation_id",
  "provider",
  "model",
  "timestamp",
] as const;

export function createSourceLocalityDiagnostics(options: {
  readonly operation: string;
  readonly engineAiProviderBoundary:
    | "not_applicable"
    | "engine_owned_when_configured";
  readonly limitations: readonly string[];
}): SourceLocalityDiagnostics {
  return {
    locality_policy_version: SOURCE_LOCALITY_POLICY_VERSION,
    operation: options.operation,
    extension_source_upload: false,
    extension_source_network: false,
    telemetry_source_fields: false,
    analytics_source_fields: false,
    cloud_client_used: false,
    data_lake_client_used: false,
    extension_ai_client_used: false,
    engine_ai_provider_boundary: options.engineAiProviderBoundary,
    source_mutation_detected: false,
    git_mutation_detected: false,
    identity_used: false,
    provider_credentials_extension_owned: false,
    limitations: [...options.limitations].sort(),
  };
}

export function sourceLocalityDiagnosticsToStableDict(
  diagnostics: SourceLocalityDiagnostics
): Record<string, unknown> {
  return {
    analytics_source_fields: diagnostics.analytics_source_fields,
    cloud_client_used: diagnostics.cloud_client_used,
    data_lake_client_used: diagnostics.data_lake_client_used,
    engine_ai_provider_boundary: diagnostics.engine_ai_provider_boundary,
    extension_ai_client_used: diagnostics.extension_ai_client_used,
    extension_source_network: diagnostics.extension_source_network,
    extension_source_upload: diagnostics.extension_source_upload,
    git_mutation_detected: diagnostics.git_mutation_detected,
    identity_used: diagnostics.identity_used,
    limitations: [...diagnostics.limitations].sort(),
    locality_policy_version: diagnostics.locality_policy_version,
    operation: diagnostics.operation,
    provider_credentials_extension_owned:
      diagnostics.provider_credentials_extension_owned,
    source_mutation_detected: diagnostics.source_mutation_detected,
    telemetry_source_fields: diagnostics.telemetry_source_fields,
  };
}

export function localityDiagnosticsContainForbiddenKeys(
  value: Record<string, unknown>
): boolean {
  const blob = JSON.stringify(value).toLowerCase();
  if (blob.includes("/users/") || blob.includes("file://")) {
    return true;
  }
  for (const key of FORBIDDEN_KEYS) {
    if (Object.prototype.hasOwnProperty.call(value, key)) {
      return true;
    }
  }
  return false;
}

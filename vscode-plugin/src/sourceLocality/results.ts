/**
 * Bounded locality result categories (Slice 13.10).
 */

export const LOCALITY_RESULT_CATEGORIES = [
  "local_only",
  "local_with_engine_ai_provider_boundary",
  "local_navigation_only",
  "unavailable",
  "violation",
] as const;

export type LocalityResultCategory =
  (typeof LOCALITY_RESULT_CATEGORIES)[number];

export const LOCALITY_OPERATIONS = [
  "discover_cli",
  "install_guidance",
  "initialize_repository",
  "run_assessment",
  "run_assessment_with_ai",
  "open_report",
  "recovery",
  "doctor",
  "activation",
  "open_documentation",
] as const;

export type LocalityOperation = (typeof LOCALITY_OPERATIONS)[number];

/** Engine-owned generated artifact classes (no paths). */
export const GENERATED_ARTIFACT_CLASSES = [
  "local_config_artifact",
  "local_assessment_artifact",
  "local_report_artifact",
  "local_ai_artifact",
] as const;

export type GeneratedArtifactClass =
  (typeof GENERATED_ARTIFACT_CLASSES)[number];

export const APPROVED_ENGINE_ARTIFACT_BASENAMES = [
  "codestrata.toml",
  "report.json",
  "assessment.html",
  "report.html",
  "report.txt",
] as const;

export type SourceLocalityResult = {
  readonly operation: LocalityOperation;
  readonly category: LocalityResultCategory;
  readonly source_read_category:
    | "none"
    | "codestrata_config_metadata"
    | "generated_report_stat";
  readonly source_write_category: "none" | "engine_owned_via_cli";
  readonly extension_network_category:
    | "none"
    | "documentation_navigation"
    | "local_file_uri_open";
  readonly engine_network_category:
    | "none"
    | "local_only"
    | "configured_ai_provider_possible";
  readonly telemetry_category: "unavailable_or_privacy_projected";
  readonly analytics_category: "unavailable_or_privacy_projected";
  readonly generated_artifact_category: GeneratedArtifactClass | "none";
  readonly source_mutation_detected: false;
  readonly git_mutation_detected: false;
  readonly identity_used: false;
  readonly credential_used: false;
  readonly limitations: readonly string[];
};

export function createSourceLocalityResult(
  partial: Omit<
    SourceLocalityResult,
    | "source_mutation_detected"
    | "git_mutation_detected"
    | "identity_used"
    | "credential_used"
    | "limitations"
  > & { readonly limitations?: readonly string[] }
): SourceLocalityResult {
  return {
    ...partial,
    source_mutation_detected: false,
    git_mutation_detected: false,
    identity_used: false,
    credential_used: false,
    limitations: [...(partial.limitations ?? [])].sort(),
  };
}

export function sourceLocalityResultToStableDict(
  result: SourceLocalityResult
): Record<string, unknown> {
  return {
    analytics_category: result.analytics_category,
    category: result.category,
    credential_used: result.credential_used,
    engine_network_category: result.engine_network_category,
    extension_network_category: result.extension_network_category,
    generated_artifact_category: result.generated_artifact_category,
    git_mutation_detected: result.git_mutation_detected,
    identity_used: result.identity_used,
    limitations: [...result.limitations].sort(),
    operation: result.operation,
    source_mutation_detected: result.source_mutation_detected,
    source_read_category: result.source_read_category,
    source_write_category: result.source_write_category,
    telemetry_category: result.telemetry_category,
  };
}

/** Canonical operation → expected locality category. */
export function expectedCategoryForOperation(
  operation: LocalityOperation
): LocalityResultCategory {
  switch (operation) {
    case "run_assessment_with_ai":
      return "local_with_engine_ai_provider_boundary";
    case "open_documentation":
    case "install_guidance":
      return "local_navigation_only";
    case "activation":
      return "local_only";
    default:
      return "local_only";
  }
}

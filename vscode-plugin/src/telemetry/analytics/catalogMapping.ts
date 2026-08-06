/**
 * Conceptual Engine analytics catalog relationship (Epic 10 Slice 10.7).
 * No Python imports. No runtime coupling.
 */

export type EngineAnalyticsCatalogNote = {
  readonly engineClientName: "codestrata_cli";
  readonly vscodeClientName: "vscode_extension";
  readonly engineSchemaOwner: "python";
  readonly vscodeSchemaOwner: "typescript";
  readonly schemasIdentical: false;
  readonly engineMayUseInstallationIdentity: true;
  readonly vscodeIdentityFreeInSlice107: true;
  readonly engineHasProviderModelAnalytics: true;
  readonly vscodeCollectsProviderModel: false;
  readonly vscodeHttpTransport: "unavailable";
  readonly sharedConcepts: readonly string[];
  readonly intentionalDifferences: readonly string[];
};

export function describeEngineAnalyticsCatalogMapping(): EngineAnalyticsCatalogNote {
  return {
    engineClientName: "codestrata_cli",
    vscodeClientName: "vscode_extension",
    engineSchemaOwner: "python",
    vscodeSchemaOwner: "typescript",
    schemasIdentical: false,
    engineMayUseInstallationIdentity: true,
    vscodeIdentityFreeInSlice107: true,
    engineHasProviderModelAnalytics: true,
    vscodeCollectsProviderModel: false,
    vscodeHttpTransport: "unavailable",
    sharedConcepts: [
      "client",
      "version",
      "operation_category",
      "lifecycle",
      "outcome",
      "duration_bucket",
      "ai_used",
      "schema_version",
      "policy_version",
    ].sort(),
    intentionalDifferences: [
      "vscode_identity_free",
      "engine_may_carry_installation_identity_in_local_envelope",
      "schemas_independently_versioned",
      "vscode_no_provider_model_token_cost",
      "vscode_no_http_analytics_transport",
      "vscode_operation_categories_assess_and_assess_with_ai",
    ].sort(),
  };
}

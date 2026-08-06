/**
 * Conceptual reconciliation against the public Engine telemetry catalog.
 * Does not import Engine Python. Schemas remain independently versioned.
 */

export const ENGINE_CATALOG_EVENT_TYPES = [
  "application_started",
  "application_completed",
  "feature_invoked",
  "feature_completed",
  "operation_failed",
] as const;

export const VSCODE_RUNTIME_EVENT_TYPES = [
  "feature_invoked",
  "feature_completed",
  "operation_failed",
] as const;

export const SHARED_CONCEPTUAL_FIELDS = [
  "event_type",
  "lifecycle",
  "result",
  "duration_bucket",
  "operation_category",
  "offline_mode",
  "ai_used",
  "os_family",
] as const;

export type CatalogMappingNote = {
  readonly engineClientName: "codestrata_cli";
  readonly vscodeClientName: "vscode_extension";
  readonly relationship: string;
  readonly sharedEventTypes: readonly string[];
  readonly vscodeOnlyFields: readonly string[];
  readonly engineOnlyEventTypes: readonly string[];
  readonly deferred: readonly string[];
};

export function describeEngineCatalogMapping(): CatalogMappingNote {
  const shared = VSCODE_RUNTIME_EVENT_TYPES.filter((name) =>
    (ENGINE_CATALOG_EVENT_TYPES as readonly string[]).includes(name)
  );
  return {
    engineClientName: "codestrata_cli",
    vscodeClientName: "vscode_extension",
    relationship:
      "VS Code runtime uses the public Engine catalog as a conceptual field/event vocabulary reference. Schemas are independently versioned and not identical.",
    sharedEventTypes: shared,
    vscodeOnlyFields: ["extension_version"],
    engineOnlyEventTypes: ["application_started", "application_completed"],
    deferred: [
      "platform_extension_event_schema_mapping",
      "http_transport",
      "installation_identity",
    ],
  };
}

export function vscodeEventTypesSubsetOfEngineCatalog(): boolean {
  return VSCODE_RUNTIME_EVENT_TYPES.every((name) =>
    (ENGINE_CATALOG_EVENT_TYPES as readonly string[]).includes(name)
  );
}

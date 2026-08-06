/**
 * VS Code analytics schema compatibility (Epic 10 Slice 10.7).
 */

import { VsCodeAnalyticsError } from "./errors";
import { COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION } from "./runtimePolicy";

const COMPATIBLE = new Set([COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION]);

export function compatibleVsCodeAnalyticsSchemaVersions(): readonly string[] {
  return [...COMPATIBLE].sort();
}

export function assertVsCodeAnalyticsSchemaCompatible(
  schemaVersion: string
): void {
  if (!COMPATIBLE.has(schemaVersion)) {
    throw new VsCodeAnalyticsError("incompatible_schema");
  }
}

/** No-op migration hook for schema 1.0 only. */
export function migrateVsCodeAnalyticsMapping(
  payload: Record<string, unknown>
): Record<string, unknown> {
  const version = payload.schema_version;
  if (typeof version !== "string") {
    throw new VsCodeAnalyticsError("incompatible_schema");
  }
  assertVsCodeAnalyticsSchemaCompatible(version);
  return { ...payload };
}

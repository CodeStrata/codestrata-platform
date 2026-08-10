/** Report schema compatibility for public report.json (schema 1.2 family). */

export const SUPPORTED_SCHEMA_MAJOR = "1";
export const SUPPORTED_SCHEMA_DOC = "1.2";

export type SchemaCompatibility =
  | { ok: true; schemaVersion?: string }
  | { ok: false; schemaVersion?: string; reason: string };

export function checkReportSchemaVersion(schemaVersion: unknown): SchemaCompatibility {
  if (schemaVersion == null || schemaVersion === "") {
    // Older fixtures may omit manifest.schema_version — tolerate with caution.
    return { ok: true, schemaVersion: undefined };
  }
  const version = String(schemaVersion).trim();
  const major = version.split(".", 1)[0];
  if (major !== SUPPORTED_SCHEMA_MAJOR) {
    return {
      ok: false,
      schemaVersion: version,
      reason:
        `Unsupported Engineering Assessment report schema ${version}. ` +
        `This CodeStrata VS Code Extension supports schema ${SUPPORTED_SCHEMA_DOC} (major ${SUPPORTED_SCHEMA_MAJOR}.x).`,
    };
  }
  return { ok: true, schemaVersion: version };
}

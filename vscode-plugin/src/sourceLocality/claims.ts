/**
 * Authoritative data-flow statements (Slice 13.10).
 * Used by docs and tests — keep precise, not marketing.
 */

export const SOURCE_LOCALITY_CLAIMS = {
  extension_no_source_upload:
    "The VS Code extension does not upload repository source to CodeStrata Community services.",
  standard_assessment_local:
    "CodeStrata assessments are executed locally by the CodeStrata CLI. The VS Code extension does not upload repository source to CodeStrata Community services.",
  ai_provider_engine_owned:
    "When AI enrichment is enabled, the local Engine may send provider request content to the configured AI provider according to that provider configuration.",
  extension_no_ai_client:
    "The VS Code extension does not import AI-provider SDKs, resolve provider API keys, or construct provider requests.",
  telemetry_no_source:
    "VS Code telemetry and analytics exclude source, paths, report contents, findings, evidence, credentials, and machine/install identity.",
  docs_navigation_only:
    "Opening a fixed documentation URL via openExternal is navigation, not repository transmission.",
} as const;

/** Claims that must NOT appear in privacy/docs without AI qualification. */
export const FORBIDDEN_OVERCLAIMS = [
  "never leaves your machine",
  "source code never leaves",
  "all ai data always stays local",
  "ai assessment sends no data off machine",
] as const;

export function claimsToStableDict(): Record<string, unknown> {
  return {
    ai_provider_engine_owned: SOURCE_LOCALITY_CLAIMS.ai_provider_engine_owned,
    docs_navigation_only: SOURCE_LOCALITY_CLAIMS.docs_navigation_only,
    extension_no_ai_client: SOURCE_LOCALITY_CLAIMS.extension_no_ai_client,
    extension_no_source_upload:
      SOURCE_LOCALITY_CLAIMS.extension_no_source_upload,
    forbidden_overclaims: [...FORBIDDEN_OVERCLAIMS].sort(),
    standard_assessment_local:
      SOURCE_LOCALITY_CLAIMS.standard_assessment_local,
    telemetry_no_source: SOURCE_LOCALITY_CLAIMS.telemetry_no_source,
  };
}

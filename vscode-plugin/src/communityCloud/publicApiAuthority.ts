/**
 * Public Community Cloud API authority (Slice 17.14).
 *
 * VS Code never calls Insights admin APIs from the browser/extension UI
 * for Community telemetry. When Community Cloud transport is explicitly
 * configured for production, the branded hostname is authoritative.
 */
export const PUBLIC_COMMUNITY_API_HOSTNAME = "api.codestrata.ai";
export const PUBLIC_COMMUNITY_API_BASE_URL = "https://api.codestrata.ai";
export const PUBLIC_COMMUNITY_API_REGION = "us-west-2";

/** Optional local/dev override. Must not be an execute-api hostname. */
export const COMMUNITY_API_BASE_ENV = "CODESTRATA_COMMUNITY_CLOUD_API_BASE";

export const PUBLIC_EXTENSION_EVENTS_PATH = "/api/v1/extension-events";
export const PUBLIC_TELEMETRY_PATH = "/api/v1/telemetry";

export function isPublicCommunityApiHost(hostname: string | undefined | null): boolean {
  return (hostname || "").trim().toLowerCase().replace(/\.$/, "") === PUBLIC_COMMUNITY_API_HOSTNAME;
}

export function isExecuteApiImplementationHost(hostname: string | undefined | null): boolean {
  const host = (hostname || "").trim().toLowerCase();
  return host.includes("execute-api.") && host.includes(".amazonaws.com");
}

/**
 * Resolve production Community API base URL.
 * Local/dev may set CODESTRATA_COMMUNITY_CLOUD_API_BASE; execute-api is rejected.
 */
export function resolvePublicCommunityApiBase(
  env: NodeJS.ProcessEnv | Record<string, string | undefined> = process.env,
): string {
  const override = (env[COMMUNITY_API_BASE_ENV] || "").trim().replace(/\/$/, "");
  if (!override) {
    return PUBLIC_COMMUNITY_API_BASE_URL;
  }
  let host = "";
  try {
    host = new URL(override).hostname;
  } catch {
    throw new Error(`${COMMUNITY_API_BASE_ENV} must be an absolute https URL`);
  }
  if (isExecuteApiImplementationHost(host)) {
    throw new Error(
      `${COMMUNITY_API_BASE_ENV} must not use execute-api hostname; use ${PUBLIC_COMMUNITY_API_BASE_URL}`,
    );
  }
  return override;
}

export function productionExtensionEventsUrl(
  env: NodeJS.ProcessEnv | Record<string, string | undefined> = process.env,
): string {
  return `${resolvePublicCommunityApiBase(env)}${PUBLIC_EXTENSION_EVENTS_PATH}`;
}

export function productionTelemetryIngestUrl(
  env: NodeJS.ProcessEnv | Record<string, string | undefined> = process.env,
): string {
  return `${resolvePublicCommunityApiBase(env)}${PUBLIC_TELEMETRY_PATH}`;
}

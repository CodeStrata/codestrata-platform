/**
 * Community Cloud projection readiness (Slice 15.4).
 * Transmission remains disabled; identity projection is activation-ready.
 * Public API hostname authority: Slice 17.14.
 * Report publish/share UI: Slice 17.21 (`codestrata.publishCurrentReport`).
 */

export {
  COMMUNITY_CLOUD_IDENTITY_FILENAME,
  COMMUNITY_CLOUD_IDENTITY_POLICY,
  codestrataHomeDir,
  installationIdentityFilePath,
  loadSharedAnonymousInstallationId,
  tryLoadSharedAnonymousInstallationId,
} from "./installationIdentity";

export {
  COMMUNITY_API_BASE_ENV,
  PUBLIC_COMMUNITY_API_BASE_URL,
  PUBLIC_COMMUNITY_API_HOSTNAME,
  PUBLIC_COMMUNITY_API_REGION,
  PUBLIC_EXTENSION_EVENTS_PATH,
  PUBLIC_TELEMETRY_PATH,
  isExecuteApiImplementationHost,
  isPublicCommunityApiHost,
  productionExtensionEventsUrl,
  productionTelemetryIngestUrl,
  resolvePublicCommunityApiBase,
} from "./publicApiAuthority";

/**
 * Community Cloud installation identity reader (Slice 15.4 / CR-15.3-003).
 *
 * Reads the Engine-owned anonymous installation identity file shared via
 * CODESTRATA_HOME / ~/.codestrata. Does NOT use VS Code machineId, device ID,
 * hostname, or username. Does NOT mint a second tracking identity.
 *
 * Transmission remains disabled — this module is activation-ready for future
 * Community Cloud extension_event projection only.
 */

import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

export const COMMUNITY_CLOUD_IDENTITY_FILENAME =
  "anonymous-installation-identity.json";

export const COMMUNITY_CLOUD_IDENTITY_POLICY = {
  usesEngineSharedIdentity: true as const,
  mintSecondIdentityForbidden: true as const,
  machineIdForbidden: true as const,
  transmissionEnabled: false as const,
  activationReady: true as const,
};

const UUID_V4_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function codestrataHomeDir(
  env: NodeJS.ProcessEnv = process.env
): string {
  const override = (env.CODESTRATA_HOME || "").trim();
  if (override) {
    return override;
  }
  return path.join(os.homedir(), ".codestrata");
}

export function installationIdentityFilePath(
  env: NodeJS.ProcessEnv = process.env
): string {
  return path.join(codestrataHomeDir(env), COMMUNITY_CLOUD_IDENTITY_FILENAME);
}

export type LoadedCommunityInstallationIdentity = {
  readonly installationId: string;
  readonly source: "engine_shared_file";
};

/**
 * Load the approved Engine anonymous installation id when present and valid.
 * Returns undefined when absent/unreadable/invalid — never invents an id.
 */
export function loadSharedAnonymousInstallationId(
  env: NodeJS.ProcessEnv = process.env
): LoadedCommunityInstallationIdentity | undefined {
  const filePath = installationIdentityFilePath(env);
  let raw: string;
  try {
    raw = fs.readFileSync(filePath, "utf8");
  } catch {
    return undefined;
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return undefined;
  }
  if (!parsed || typeof parsed !== "object") {
    return undefined;
  }
  const id = (parsed as { installation_id?: unknown }).installation_id;
  if (typeof id !== "string" || !UUID_V4_RE.test(id.trim())) {
    return undefined;
  }
  return {
    installationId: id.trim(),
    source: "engine_shared_file",
  };
}

/** Fail-soft wrapper — never throws into assessment/CLI paths. */
export function tryLoadSharedAnonymousInstallationId(
  env: NodeJS.ProcessEnv = process.env
): LoadedCommunityInstallationIdentity | undefined {
  try {
    return loadSharedAnonymousInstallationId(env);
  } catch {
    return undefined;
  }
}

/** Engine CLI version compatibility — delegates to Slice 13.11 matrix. */

import { evaluateCliCompatibility } from "../cliCompatibility";

export const MIN_ENGINE_VERSION = "0.2.0";
export const SUPPORTED_ENGINE_VERSION_RANGE = "0.2.x (major 0, minor 2)";
export const SUPPORTED_REPORT_SCHEMA = "1.2";

export interface EngineVersionInfo {
  raw: string;
  version?: string;
  compatible: boolean;
  reason?: string;
}

/**
 * Parse short identity line `CodeStrata X.Y.Z` (or first line of version output).
 * Strict identity required — do not accept bare semver from arbitrary executables.
 */
export function parseEngineVersionOutput(stdout: string): EngineVersionInfo {
  const raw = stdout.trim();
  const firstLine =
    raw
      .split(/\r?\n/)
      .map((line) => line.trim())
      .find(Boolean) ?? "";
  const match = firstLine.match(
    /^CodeStrata\s+(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)\s*$/
  );
  if (!match) {
    return {
      raw,
      compatible: false,
      reason:
        "Could not parse CodeStrata Engine identity/version. Set codestrata.engine.executable to a valid CodeStrata CLI.",
    };
  }
  const version = match[1];
  const compatible = isCompatibleEngineVersion(version);
  return {
    raw,
    version,
    compatible,
    reason: compatible
      ? undefined
      : `Engine ${version} is outside the supported range ${SUPPORTED_ENGINE_VERSION_RANGE} for this extension.`,
  };
}

export function isCompatibleEngineVersion(version: string): boolean {
  return evaluateCliCompatibility({ cliVersion: version }).supported;
}

/** Engine CLI version compatibility for the Community VS Code Extension. */

export const MIN_ENGINE_VERSION = "0.1.0";
export const SUPPORTED_ENGINE_VERSION_RANGE = ">=0.1.0 <2.0.0";
export const SUPPORTED_REPORT_SCHEMA = "1.2";

export interface EngineVersionInfo {
  raw: string;
  version?: string;
  compatible: boolean;
  reason?: string;
}

/** Parse `codestrata version` stdout (first line often `CodeStrata 0.1.0`). */
export function parseEngineVersionOutput(stdout: string): EngineVersionInfo {
  const raw = stdout.trim();
  const match =
    raw.match(/CodeStrata\s+(\d+\.\d+\.\d+[^\s]*)/i) ||
    raw.match(/CLI:\s*(\d+\.\d+\.\d+[^\s]*)/i) ||
    raw.match(/\b(\d+\.\d+\.\d+)\b/);
  if (!match) {
    return {
      raw,
      compatible: false,
      reason:
        "Could not parse CodeStrata Engine version. Upgrade Engine or set codestrata.engine.executable.",
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
  const parsed = parseSemver(version);
  if (!parsed) {
    return false;
  }
  const min = { major: 0, minor: 1, patch: 0 };
  const maxExclusiveMajor = 2;
  if (parsed.major >= maxExclusiveMajor) {
    return false;
  }
  return compareSemver(parsed, min) >= 0;
}

function compareSemver(
  a: { major: number; minor: number; patch: number },
  b: { major: number; minor: number; patch: number }
): number {
  if (a.major !== b.major) {
    return a.major - b.major;
  }
  if (a.minor !== b.minor) {
    return a.minor - b.minor;
  }
  return a.patch - b.patch;
}

function parseSemver(
  version: string
): { major: number; minor: number; patch: number } | undefined {
  const match = version.trim().match(/^(\d+)\.(\d+)\.(\d+)/);
  if (!match) {
    return undefined;
  }
  return {
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3]),
  };
}

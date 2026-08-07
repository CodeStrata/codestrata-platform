/** Strict semantic version parsing (Slice 13.2). No lexical comparison. */

export type SemanticVersion = {
  readonly major: number;
  readonly minor: number;
  readonly patch: number;
  readonly prerelease?: string;
  readonly build?: string;
};

const SEMVER_RE =
  /^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$/;

const MAX_COMPONENT = 1_000_000;

export function parseSemanticVersion(
  value: string
): SemanticVersion | undefined {
  const trimmed = value.trim();
  if (!trimmed || /[^\x20-\x7E]/.test(trimmed)) {
    return undefined;
  }
  const match = trimmed.match(SEMVER_RE);
  if (!match) {
    return undefined;
  }
  const major = Number(match[1]);
  const minor = Number(match[2]);
  const patch = Number(match[3]);
  if (
    !Number.isInteger(major) ||
    !Number.isInteger(minor) ||
    !Number.isInteger(patch) ||
    major < 0 ||
    minor < 0 ||
    patch < 0 ||
    major > MAX_COMPONENT ||
    minor > MAX_COMPONENT ||
    patch > MAX_COMPONENT
  ) {
    return undefined;
  }
  const result: SemanticVersion = { major, minor, patch };
  if (match[4]) {
    if (!/^[0-9A-Za-z.-]+$/.test(match[4])) {
      return undefined;
    }
    return { ...result, prerelease: match[4], ...(match[5] ? { build: match[5] } : {}) };
  }
  if (match[5]) {
    if (!/^[0-9A-Za-z.-]+$/.test(match[5])) {
      return undefined;
    }
    return { ...result, build: match[5] };
  }
  return result;
}

export function compareSemanticVersion(
  a: SemanticVersion,
  b: SemanticVersion
): number {
  if (a.major !== b.major) {
    return a.major - b.major;
  }
  if (a.minor !== b.minor) {
    return a.minor - b.minor;
  }
  return a.patch - b.patch;
}

export function formatSemanticVersion(version: SemanticVersion): string {
  let text = `${version.major}.${version.minor}.${version.patch}`;
  if (version.prerelease) {
    text += `-${version.prerelease}`;
  }
  if (version.build) {
    text += `+${version.build}`;
  }
  return text;
}

export function semanticVersionToStableDict(
  version: SemanticVersion
): Record<string, unknown> {
  const out: Record<string, unknown> = {
    major: version.major,
    minor: version.minor,
    patch: version.patch,
  };
  if (version.prerelease) {
    out.prerelease = version.prerelease;
  }
  if (version.build) {
    out.build = version.build;
  }
  return out;
}

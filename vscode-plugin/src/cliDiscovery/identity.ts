/**
 * Product identity validation for `codestrata version` output (Slice 13.2).
 *
 * Engine emits `CodeStrata X.Y.Z` as the first line (format_version_line).
 * Do not accept arbitrary executables that merely print a semver.
 */

import {
  parseSemanticVersion,
  type SemanticVersion,
} from "./versions";

export const PRODUCT_IDENTITY_TOKEN = "CodeStrata" as const;

/** First line must be exactly: CodeStrata <semver> */
const IDENTITY_LINE_RE =
  /^CodeStrata\s+(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)\s*$/;

export type IdentityParseResult =
  | {
      readonly ok: true;
      readonly version: SemanticVersion;
      readonly versionText: string;
    }
  | {
      readonly ok: false;
      readonly reason:
        | "empty_output"
        | "identity_mismatch"
        | "malformed_version"
        | "contradictory_versions"
        | "excessive_output";
    };

export function parseProductIdentityOutput(
  stdout: string,
  options?: { readonly maxBytes?: number }
): IdentityParseResult {
  const maxBytes = options?.maxBytes ?? 65_536;
  if (Buffer.byteLength(stdout, "utf8") > maxBytes) {
    return { ok: false, reason: "excessive_output" };
  }
  const lines = stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length === 0) {
    return { ok: false, reason: "empty_output" };
  }

  const first = lines[0];
  if (/[^\x20-\x7E]/.test(first)) {
    return { ok: false, reason: "identity_mismatch" };
  }
  const match = first.match(IDENTITY_LINE_RE);
  if (!match) {
    return { ok: false, reason: "identity_mismatch" };
  }
  const version = parseSemanticVersion(match[1]);
  if (!version) {
    return { ok: false, reason: "malformed_version" };
  }

  // Reject contradictory CodeStrata version lines later in the payload.
  for (const line of lines.slice(1)) {
    const other = line.match(IDENTITY_LINE_RE);
    if (other && other[1] !== match[1]) {
      return { ok: false, reason: "contradictory_versions" };
    }
    const cliLine = line.match(/^CLI:\s*(\d+\.\d+\.\d+[^\s]*)$/i);
    if (cliLine) {
      const cliVersion = parseSemanticVersion(cliLine[1]);
      if (
        cliVersion &&
        (cliVersion.major !== version.major ||
          cliVersion.minor !== version.minor ||
          cliVersion.patch !== version.patch)
      ) {
        return { ok: false, reason: "contradictory_versions" };
      }
    }
  }

  return { ok: true, version, versionText: match[1] };
}

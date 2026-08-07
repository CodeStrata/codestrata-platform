/**
 * Local initialization-state detection (Slice 13.4).
 *
 * Minimal structural checks only — does not duplicate Engine config business logic.
 * Does not mutate files.
 */

import * as fs from "node:fs";
import * as path from "node:path";

import { CODESTRATA_CONFIG_BASENAME } from "./policy";
import type { RepositoryInitState } from "./states";

export type DetectInitStateInput = {
  readonly workspaceRoot: string;
  /** Relative or absolute config path; empty → codestrata.toml in workspace. */
  readonly configuredConfigPath?: string;
};

export type DetectInitStateResult = {
  readonly state: RepositoryInitState;
  /** Private runtime path — never put in public diagnostics. */
  readonly configPath: string;
};

/**
 * Resolve the expected configuration path for a workspace.
 * Empty/default → `<workspace>/codestrata.toml`.
 */
export function resolveConfigPath(
  workspaceRoot: string,
  configuredConfigPath?: string
): string {
  const trimmed = (configuredConfigPath ?? "").trim();
  if (!trimmed) {
    return path.join(workspaceRoot, CODESTRATA_CONFIG_BASENAME);
  }
  if (path.isAbsolute(trimmed)) {
    return trimmed;
  }
  return path.join(workspaceRoot, trimmed);
}

/**
 * Structural validity for a CodeStrata Engine init artifact.
 * Requires UTF-8 text with a `[repository]` table marker.
 */
export function classifyConfigContents(contents: string): RepositoryInitState {
  if (!contents || !contents.trim()) {
    return "partial_initialization";
  }
  if (/[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]/.test(contents) && contents.includes("\u0000")) {
    return "invalid_configuration";
  }
  const hasRepository = /^\s*\[repository\]\s*$/m.test(contents);
  if (!hasRepository) {
    // File exists with content but missing the Engine init marker.
    return "invalid_configuration";
  }
  // Soft check: community profile is part of Engine minimal template but not required
  // for "initialized" — presence of [repository] is enough structural signal.
  return "initialized";
}

export function detectRepositoryInitState(
  input: DetectInitStateInput
): DetectInitStateResult {
  const configPath = resolveConfigPath(
    input.workspaceRoot,
    input.configuredConfigPath
  );
  try {
    if (!fs.existsSync(configPath)) {
      return { state: "not_initialized", configPath };
    }
    const stat = fs.statSync(configPath);
    if (!stat.isFile()) {
      return { state: "invalid_configuration", configPath };
    }
    if (stat.size === 0) {
      return { state: "partial_initialization", configPath };
    }
    const contents = fs.readFileSync(configPath, "utf8");
    return { state: classifyConfigContents(contents), configPath };
  } catch {
    return { state: "unknown", configPath };
  }
}

/** Ensure init CLI args never include --force / -f overwrite. */
export function assertInitArgsForbidForce(args: readonly string[]): void {
  for (const token of args) {
    if (token === "--force" || token === "-f") {
      throw new Error("force_overwrite_forbidden");
    }
  }
}

/**
 * Candidate listing for CLI discovery (Slice 13.2).
 *
 * No arbitrary filesystem crawl. Development candidates are limited to
 * workspace `.venv` and active VIRTUAL_ENV / CONDA_PREFIX (existing contract).
 */

import * as fs from "node:fs";
import * as path from "node:path";

import { isPathStyleCandidate } from "./executableValidation";
import type { CliCandidateSource } from "./sources";

export const DEFAULT_CLI_COMMAND_NAME = "codestrata" as const;

export type DiscoveryCandidate = {
  readonly command: string;
  readonly source: Exclude<CliCandidateSource, "unavailable">;
  readonly requiresFilesystemValidation: boolean;
};

export type ListCandidatesInput = {
  readonly configuredExecutable: string;
  readonly workspaceFolders: readonly string[];
  readonly env?: NodeJS.ProcessEnv;
  readonly platform?: NodeJS.Platform;
  readonly maxCandidates?: number;
};

function exeName(platform: NodeJS.Platform): string {
  return platform === "win32" ? "codestrata.exe" : "codestrata";
}

function venvBin(platform: NodeJS.Platform): string {
  return platform === "win32" ? "Scripts" : "bin";
}

/**
 * Build ordered candidates.
 * If an explicit configuration is present, it is the only candidate returned
 * (fail-closed — callers must not PATH-fallback after explicit failure).
 */
export function listDiscoveryCandidates(
  input: ListCandidatesInput
): DiscoveryCandidate[] {
  const platform = input.platform ?? process.platform;
  const env = input.env ?? process.env;
  const max = input.maxCandidates ?? 8;
  const configured = (input.configuredExecutable ?? "").trim();
  const candidates: DiscoveryCandidate[] = [];
  const seen = new Set<string>();

  const push = (candidate: DiscoveryCandidate): void => {
    if (candidates.length >= max) {
      return;
    }
    const key = path.normalize(candidate.command);
    if (!key || seen.has(key)) {
      return;
    }
    seen.add(key);
    candidates.push(candidate);
  };

  const isDefaultName =
    !configured ||
    configured === DEFAULT_CLI_COMMAND_NAME ||
    configured === "codestrata.exe";

  if (configured && !isDefaultName) {
    // Explicit configuration — sole candidate (fail closed).
    push({
      command: configured,
      source: "explicit_configuration",
      requiresFilesystemValidation: isPathStyleCandidate(configured),
    });
    return candidates;
  }

  // Development environment (existing product contract — not arbitrary crawl).
  for (const folder of input.workspaceFolders) {
    const venvPath = path.join(
      folder,
      ".venv",
      venvBin(platform),
      exeName(platform)
    );
    if (fs.existsSync(venvPath)) {
      push({
        command: venvPath,
        source: "development_environment",
        requiresFilesystemValidation: true,
      });
    }
  }

  for (const envRoot of [env.VIRTUAL_ENV, env.CONDA_PREFIX]) {
    if (!envRoot) {
      continue;
    }
    const activePath = path.join(
      envRoot,
      venvBin(platform),
      exeName(platform)
    );
    if (fs.existsSync(activePath)) {
      push({
        command: activePath,
        source: "development_environment",
        requiresFilesystemValidation: true,
      });
    }
  }

  // PATH lookup via direct spawn of command name (no shell which/where).
  push({
    command: DEFAULT_CLI_COMMAND_NAME,
    source: "process_path",
    requiresFilesystemValidation: false,
  });

  return candidates;
}

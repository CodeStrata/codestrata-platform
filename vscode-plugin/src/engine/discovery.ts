/**
 * Legacy Engine candidate helpers.
 *
 * Slice 13.2 authoritative discovery lives in `src/cliDiscovery/`.
 * This module remains for onboarding labels and limited compatibility callers.
 */

import * as fs from "node:fs";
import * as path from "node:path";

export interface EngineCandidate {
  executable: string;
  source: "configured" | "workspace-venv" | "active-python" | "path";
}

const VENV_BIN = process.platform === "win32" ? "Scripts" : "bin";
const EXE_NAME = process.platform === "win32" ? "codestrata.exe" : "codestrata";

/**
 * @deprecated Prefer `listDiscoveryCandidates` from `cliDiscovery`.
 * Retained for compatibility with existing onboarding helpers.
 */
export function listEngineCandidates(
  configured: string,
  workspaceFolders: string[]
): EngineCandidate[] {
  const candidates: EngineCandidate[] = [];
  const seen = new Set<string>();

  const push = (executable: string, source: EngineCandidate["source"]) => {
    const normalized = path.normalize(executable);
    if (!normalized || seen.has(normalized)) {
      return;
    }
    seen.add(normalized);
    candidates.push({ executable: normalized, source });
  };

  const configuredTrim = configured.trim();
  if (configuredTrim && configuredTrim !== "codestrata" && path.isAbsolute(configuredTrim)) {
    push(configuredTrim, "configured");
  } else if (configuredTrim && configuredTrim !== "codestrata") {
    push(configuredTrim, "configured");
  }

  for (const folder of workspaceFolders) {
    const venvPath = path.join(folder, ".venv", VENV_BIN, EXE_NAME);
    if (fs.existsSync(venvPath)) {
      push(venvPath, "workspace-venv");
    }
  }

  for (const envRoot of [process.env.VIRTUAL_ENV, process.env.CONDA_PREFIX]) {
    if (!envRoot) {
      continue;
    }
    const activePath = path.join(envRoot, VENV_BIN, EXE_NAME);
    if (fs.existsSync(activePath)) {
      push(activePath, "active-python");
    }
  }

  push(
    configuredTrim && !path.isAbsolute(configuredTrim)
      ? configuredTrim
      : "codestrata",
    "path"
  );

  return candidates;
}

export function redactSecrets(text: string): string {
  return text
    .replace(/(api[_-]?key\s*[=:]\s*)\S+/gi, "$1***")
    .replace(/(authorization:\s*bearer\s+)\S+/gi, "$1***")
    .replace(/(AWS_SECRET_ACCESS_KEY\s*[=:]\s*)\S+/gi, "$1***")
    .replace(/(OPENAI_API_KEY\s*[=:]\s*)\S+/gi, "$1***");
}

/** Prefer source-only labels in user-facing text; path form is for debug helpers. */
export function formatCandidateLabel(candidate: EngineCandidate): string {
  return `${candidate.source}`;
}

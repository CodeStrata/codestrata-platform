/**
 * Resolve CodeStrata Engine CLI without silently picking an unexpected binary.
 */

import * as fs from "node:fs";
import * as path from "node:path";

export interface EngineCandidate {
  executable: string;
  source: "configured" | "workspace-venv" | "active-python" | "path";
}

export interface EngineResolution {
  selected?: EngineCandidate;
  candidates: EngineCandidate[];
  versionOutput?: string;
  error?: string;
}

const PATH_SEP = process.platform === "win32" ? ";" : ":";
const VENV_BIN = process.platform === "win32" ? "Scripts" : "bin";
const EXE_NAME = process.platform === "win32" ? "codestrata.exe" : "codestrata";

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
    // Relative configured path — resolve later against first workspace if needed.
    push(configuredTrim, "configured");
  }

  for (const folder of workspaceFolders) {
    const venvPath = path.join(folder, ".venv", VENV_BIN, EXE_NAME);
    if (fs.existsSync(venvPath)) {
      push(venvPath, "workspace-venv");
    }
  }

  // Active Python environment (VIRTUAL_ENV / CONDA_PREFIX) when Engine is installed there.
  for (const envRoot of [process.env.VIRTUAL_ENV, process.env.CONDA_PREFIX]) {
    if (!envRoot) {
      continue;
    }
    const activePath = path.join(envRoot, VENV_BIN, EXE_NAME);
    if (fs.existsSync(activePath)) {
      push(activePath, "active-python");
    }
  }

  // PATH lookup (name only — actual existence verified by version probe).
  push(configuredTrim && !path.isAbsolute(configuredTrim) ? configuredTrim : "codestrata", "path");

  return candidates;
}

export function isExecutablePresent(executable: string): boolean {
  if (path.isAbsolute(executable) || executable.includes("/") || executable.includes("\\")) {
    try {
      return fs.existsSync(executable);
    } catch {
      return false;
    }
  }
  // PATH name — cannot know without probing; treat as candidate.
  return true;
}

export function redactSecrets(text: string): string {
  return text
    .replace(/(api[_-]?key\s*[=:]\s*)\S+/gi, "$1***")
    .replace(/(authorization:\s*bearer\s+)\S+/gi, "$1***")
    .replace(/(AWS_SECRET_ACCESS_KEY\s*[=:]\s*)\S+/gi, "$1***")
    .replace(/(OPENAI_API_KEY\s*[=:]\s*)\S+/gi, "$1***");
}

export function formatCandidateLabel(candidate: EngineCandidate): string {
  return `${candidate.executable} (${candidate.source})`;
}

export function pathEntries(): string[] {
  return (process.env.PATH || "")
    .split(PATH_SEP)
    .map((entry) => entry.trim())
    .filter(Boolean);
}

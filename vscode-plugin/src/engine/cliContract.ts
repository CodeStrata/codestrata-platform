/** Public CLI contract helpers — spawn args only; no Engine internals. */

import type { CodestrataSettings } from "../config/settings";

export interface AssessOptions {
  workspaceFolder: string;
  withAi: boolean;
  settings: CodestrataSettings;
}

export interface AssessmentJsonSummary {
  repository?: string;
  mode?: string;
  duration_ms?: number;
  findings?: number;
  recommendations?: number;
  technologies?: number;
  ai_status?: string;
  ai_executed?: boolean;
  model_id?: string | null;
  html_report?: string;
  json_report?: string;
  run_directory?: string;
}

/** Args the extension always manages — stripped from extraArgs. */
export const PROTECTED_ASSESS_FLAGS = new Set([
  "assess",
  "--repo",
  "-r",
  "--output",
  "-o",
  "--with-ai",
  "--no-ai",
  "--quiet",
  "--json-summary",
]);

export function sanitizeExtraArgs(extraArgs: string[]): string[] {
  const cleaned: string[] = [];
  for (let index = 0; index < extraArgs.length; index += 1) {
    const token = extraArgs[index]?.trim();
    if (!token) {
      continue;
    }
    if (PROTECTED_ASSESS_FLAGS.has(token)) {
      // Skip flag and its value when the next token is not another flag.
      const next = extraArgs[index + 1];
      if (next && !next.startsWith("-") && (token === "--repo" || token === "-r" || token === "--output" || token === "-o" || token === "--config" || token === "-c")) {
        index += 1;
      }
      continue;
    }
    cleaned.push(token);
  }
  return cleaned;
}

export function buildAssessArgs(options: AssessOptions): string[] {
  const args = [
    "assess",
    "--repo",
    options.workspaceFolder,
    "--output",
    options.settings.outputDirectory,
    options.withAi ? "--with-ai" : "--no-ai",
    "--quiet",
    "--json-summary",
  ];
  if (options.settings.configPath) {
    args.push("--config", options.settings.configPath);
  }
  args.push(...sanitizeExtraArgs(options.settings.extraArgs));
  return args;
}

export function buildInitArgs(settings: CodestrataSettings): string[] {
  // Slice 13.4: never pass --force. Engine owns writes; overwrite is forbidden.
  const args = ["init"];
  if (settings.configPath) {
    args.push("--config", settings.configPath);
  }
  return args;
}

export function buildDoctorArgs(settings: CodestrataSettings): string[] {
  const args = ["doctor"];
  if (settings.configPath) {
    args.push("--config", settings.configPath);
  }
  return args;
}

export function buildVersionArgs(): string[] {
  return ["version"];
}

export function parseJsonSummary(stdout: string): AssessmentJsonSummary | undefined {
  const lines = stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  for (let index = lines.length - 1; index >= 0; index -= 1) {
    const line = lines[index];
    if (!line.startsWith("{")) {
      continue;
    }
    try {
      const parsed = JSON.parse(line) as AssessmentJsonSummary;
      if (parsed && (parsed.run_directory || parsed.html_report || parsed.json_report)) {
        return parsed;
      }
    } catch {
      // keep scanning
    }
  }
  return undefined;
}

export function aiOptionalGuidance(hint: string): string {
  return (
    "Optional AI uses your CodeStrata Engine provider configuration " +
    "(Bedrock/OpenAI in codestrata.toml / environment). " +
    "Deterministic Engineering Assessment does not require AI. " +
    "Do not use CodeStrata Platform API keys as AI credentials. " +
    `Provider hint: ${hint}.`
  );
}

export const ENGINE_INSTALL_HINT =
  "Install CodeStrata Engine: python -m pip install 'codestrata[mcp]' " +
  "(or pip install -e '.[mcp]' from an Engine checkout). " +
  "Then set codestrata.engine.executable if the CLI is not on PATH.";

export const ENGINE_DOCS_QUICK_START =
  "https://github.com/CodeStrata/codestrata-engine/blob/main/docs/quick-start.md";

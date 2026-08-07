/**
 * Guided CodeStrata Engine installation for Community onboarding.
 * Spawns known package managers only — no shell interpolation of user input.
 */

import { spawn } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

export type InstallMethodId = "uv-tool" | "pipx" | "pip-user";

export interface InstallMethod {
  id: InstallMethodId;
  label: string;
  executable: string;
  args: string[];
  /** Hint for where the CLI may land after install. */
  locateHints: string[];
}

export interface InstallResult {
  ok: boolean;
  method?: InstallMethod;
  stdout: string;
  stderr: string;
  exitCode: number;
  resolvedExecutable?: string;
  reason?: string;
  troubleshooting?: string[];
}

export function detectPlatform(): "windows" | "macos" | "linux" {
  if (process.platform === "win32") {
    return "windows";
  }
  if (process.platform === "darwin") {
    return "macos";
  }
  return "linux";
}

function commandExists(name: string): boolean {
  const pathEnv = process.env.PATH || "";
  const sep = process.platform === "win32" ? ";" : ":";
  const extensions =
    process.platform === "win32" ? [".exe", ".cmd", ".bat", ""] : [""];
  for (const dir of pathEnv.split(sep)) {
    for (const ext of extensions) {
      const candidate = path.join(dir, name + ext);
      try {
        if (fs.existsSync(candidate)) {
          return true;
        }
      } catch {
        // continue
      }
    }
  }
  return false;
}

function pythonCandidates(): string[] {
  if (process.platform === "win32") {
    return ["py", "python", "python3"];
  }
  return ["python3.12", "python3", "python"];
}

/** Official install preference: uv tool → pipx → pip --user. */
export function selectInstallMethods(): InstallMethod[] {
  const methods: InstallMethod[] = [];
  const packageSpec = "codestrata[mcp]";

  if (commandExists("uv")) {
    methods.push({
      id: "uv-tool",
      label: "uv tool install (recommended when uv is available)",
      executable: "uv",
      args: ["tool", "install", packageSpec],
      locateHints: [
        path.join(os.homedir(), ".local", "bin", "codestrata"),
        path.join(os.homedir(), ".cargo", "bin", "codestrata"),
      ],
    });
  }

  if (commandExists("pipx")) {
    methods.push({
      id: "pipx",
      label: "pipx install (isolated user tool)",
      executable: "pipx",
      args: ["install", packageSpec],
      locateHints: [
        path.join(os.homedir(), ".local", "bin", "codestrata"),
        path.join(os.homedir(), ".local", "pipx", "venvs", "codestrata", "bin", "codestrata"),
      ],
    });
  }

  for (const py of pythonCandidates()) {
    if (!commandExists(py)) {
      continue;
    }
    const args =
      py === "py"
        ? ["-3", "-m", "pip", "install", "--user", packageSpec]
        : ["-m", "pip", "install", "--user", packageSpec];
    methods.push({
      id: "pip-user",
      label: `${py} -m pip install --user (official Quick Start)`,
      executable: py,
      args,
      locateHints: [
        path.join(os.homedir(), ".local", "bin", "codestrata"),
        path.join(os.homedir(), "Library", "Python", "3.12", "bin", "codestrata"),
        path.join(os.homedir(), "AppData", "Roaming", "Python", "Scripts", "codestrata.exe"),
      ],
    });
    break;
  }

  return methods;
}

export function runProcess(
  executable: string,
  args: string[],
  options?: {
    cwd?: string;
    onStdout?: (chunk: string) => void;
    onStderr?: (chunk: string) => void;
    timeoutMs?: number;
  }
): Promise<{ exitCode: number; stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const child = spawn(executable, args, {
      cwd: options?.cwd,
      shell: false,
      env: process.env,
    });
    let stdout = "";
    let stderr = "";
    const timer =
      options?.timeoutMs && options.timeoutMs > 0
        ? setTimeout(() => {
            child.kill("SIGTERM");
            reject(new Error(`Timed out after ${options.timeoutMs}ms`));
          }, options.timeoutMs)
        : undefined;

    child.stdout.on("data", (buf: Buffer) => {
      const text = buf.toString("utf8");
      stdout += text;
      options?.onStdout?.(text);
    });
    child.stderr.on("data", (buf: Buffer) => {
      const text = buf.toString("utf8");
      stderr += text;
      options?.onStderr?.(text);
    });
    child.on("error", (error) => {
      if (timer) {
        clearTimeout(timer);
      }
      reject(error);
    });
    child.on("close", (code) => {
      if (timer) {
        clearTimeout(timer);
      }
      resolve({ exitCode: code ?? 1, stdout, stderr });
    });
  });
}

export async function installEngine(_options?: {
  preferredMethodId?: InstallMethodId;
  onStdout?: (chunk: string) => void;
  onStderr?: (chunk: string) => void;
}): Promise<InstallResult> {
  // Slice 13.3 Approach A — automatic package-manager installation is forbidden.
  // Use cliInstallation guidance via codestrata.installEngine instead.
  void _options;
  return {
    ok: false,
    stdout: "",
    stderr: "",
    exitCode: 1,
    reason:
      "Automatic installation is forbidden. Use CodeStrata: Install Engine for guidance-only steps (copy command, open terminal, or open documentation).",
    troubleshooting: [
      "Open Command Palette → CodeStrata: Install Engine",
      "Copy a trusted install command and run it yourself in a terminal",
      "Docs: https://github.com/CodeStrata/codestrata-engine/blob/main/docs/quick-start.md",
      "Then run CodeStrata: Check Environment or refresh CLI detection",
    ],
  };
}

function defaultTroubleshooting(): string[] {
  return [
    "Use CodeStrata: Install Engine for guidance-only installation steps.",
    "Manual install: python -m pip install 'codestrata[mcp]'",
    "Then set codestrata.engine.executable if the CLI is not on PATH.",
    "Quick Start: https://github.com/CodeStrata/codestrata-engine/blob/main/docs/quick-start.md",
  ];
}

export { defaultTroubleshooting };

export const ENGINE_DOCS_TROUBLESHOOTING =
  "https://github.com/CodeStrata/codestrata-engine/blob/main/docs/troubleshooting.md";

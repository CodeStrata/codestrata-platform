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

export async function installEngine(options?: {
  preferredMethodId?: InstallMethodId;
  onStdout?: (chunk: string) => void;
  onStderr?: (chunk: string) => void;
}): Promise<InstallResult> {
  const methods = selectInstallMethods();
  if (methods.length === 0) {
    return {
      ok: false,
      stdout: "",
      stderr: "",
      exitCode: 1,
      reason:
        "No supported installer found (uv, pipx, or Python pip). Install Python 3.12+ first.",
      troubleshooting: [
        "Install Python 3.12+ from https://www.python.org/downloads/",
        "Or install uv (https://docs.astral.sh/uv/) / pipx, then retry.",
        "Manual: python -m pip install 'codestrata[mcp]'",
        "Docs: https://github.com/CodeStrata/codestrata-engine/blob/main/docs/quick-start.md",
      ],
    };
  }

  const ordered = options?.preferredMethodId
    ? [
        ...methods.filter((m) => m.id === options.preferredMethodId),
        ...methods.filter((m) => m.id !== options.preferredMethodId),
      ]
    : methods;

  let last: InstallResult | undefined;
  for (const method of ordered) {
    try {
      const result = await runProcess(method.executable, method.args, {
        onStdout: options?.onStdout,
        onStderr: options?.onStderr,
        timeoutMs: 10 * 60 * 1000,
      });
      if (result.exitCode === 0) {
        const resolved =
          locateInstalledExecutable(method) ||
          (process.platform === "win32" ? "codestrata.exe" : "codestrata");
        return {
          ok: true,
          method,
          stdout: result.stdout,
          stderr: result.stderr,
          exitCode: 0,
          resolvedExecutable: resolved,
        };
      }
      last = {
        ok: false,
        method,
        stdout: result.stdout,
        stderr: result.stderr,
        exitCode: result.exitCode,
        reason: `${method.label} failed with exit ${result.exitCode}.`,
        troubleshooting: defaultTroubleshooting(),
      };
    } catch (error) {
      last = {
        ok: false,
        method,
        stdout: "",
        stderr: String(error),
        exitCode: 1,
        reason: `${method.label} could not start: ${String(error)}`,
        troubleshooting: defaultTroubleshooting(),
      };
    }
  }

  return (
    last ?? {
      ok: false,
      stdout: "",
      stderr: "",
      exitCode: 1,
      reason: "Engine installation failed.",
      troubleshooting: defaultTroubleshooting(),
    }
  );
}

function locateInstalledExecutable(method: InstallMethod): string | undefined {
  const exeName = process.platform === "win32" ? "codestrata.exe" : "codestrata";
  for (const hint of method.locateHints) {
    if (fs.existsSync(hint)) {
      return hint;
    }
  }
  // PATH name — discovery will probe later.
  return exeName.replace(/\.exe$/i, "") === "codestrata" ? "codestrata" : exeName;
}

function defaultTroubleshooting(): string[] {
  return [
    "Ensure Python 3.12+ is installed and on PATH.",
    "Retry with CodeStrata: Install CodeStrata Engine.",
    "Manual install: python -m pip install 'codestrata[mcp]'",
    "Then set codestrata.engine.executable to the absolute path if needed.",
    "Quick Start: https://github.com/CodeStrata/codestrata-engine/blob/main/docs/quick-start.md",
  ];
}

export const ENGINE_DOCS_TROUBLESHOOTING =
  "https://github.com/CodeStrata/codestrata-engine/blob/main/docs/troubleshooting.md";

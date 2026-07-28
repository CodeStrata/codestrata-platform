import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";

export interface CliRunResult {
  exitCode: number;
  stdout: string;
  stderr: string;
  cancelled: boolean;
}

export interface CliRunOptions {
  executable: string;
  args: string[];
  cwd: string;
  env?: NodeJS.ProcessEnv;
  onStdout?: (chunk: string) => void;
  onStderr?: (chunk: string) => void;
  /** When aborted, terminate the child and resolve with cancelled=true. */
  signal?: AbortSignal;
}

/**
 * Run the CodeStrata Engine CLI (public interface). Never imports Engine Python modules.
 * Uses spawn with shell:false and an args array (no shell interpolation).
 */
export function runCodestrataCli(options: CliRunOptions): Promise<CliRunResult> {
  return new Promise((resolve, reject) => {
    if (options.signal?.aborted) {
      resolve({ exitCode: 0, stdout: "", stderr: "", cancelled: true });
      return;
    }

    let child: ChildProcessWithoutNullStreams;
    try {
      child = spawn(options.executable, options.args, {
        cwd: options.cwd,
        env: { ...process.env, ...options.env },
        shell: false,
        windowsHide: true,
      });
    } catch (error) {
      reject(error);
      return;
    }

    let stdout = "";
    let stderr = "";
    let settled = false;
    let cancelled = false;

    const finish = (exitCode: number) => {
      if (settled) {
        return;
      }
      settled = true;
      options.signal?.removeEventListener("abort", onAbort);
      resolve({
        exitCode,
        stdout,
        stderr,
        cancelled,
      });
    };

    const onAbort = () => {
      cancelled = true;
      try {
        child.kill("SIGTERM");
      } catch {
        // ignore
      }
      // Force kill shortly after if still running.
      setTimeout(() => {
        try {
          if (!child.killed) {
            child.kill("SIGKILL");
          }
        } catch {
          // ignore
        }
      }, 1500).unref?.();
    };

    options.signal?.addEventListener("abort", onAbort, { once: true });

    child.stdout.on("data", (buf: Buffer) => {
      const text = buf.toString("utf8");
      stdout += text;
      options.onStdout?.(text);
    });
    child.stderr.on("data", (buf: Buffer) => {
      const text = buf.toString("utf8");
      stderr += text;
      options.onStderr?.(text);
    });
    child.on("error", (error) => {
      options.signal?.removeEventListener("abort", onAbort);
      if (cancelled) {
        finish(0);
        return;
      }
      reject(error);
    });
    child.on("close", (code) => {
      finish(code ?? (cancelled ? 0 : 1));
    });
  });
}

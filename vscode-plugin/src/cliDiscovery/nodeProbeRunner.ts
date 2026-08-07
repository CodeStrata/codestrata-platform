/**
 * Node child_process probe runner (infrastructure boundary).
 * shell: false; structured args; timeout; bounded output.
 */

import { spawn } from "node:child_process";

import type { ProbeRunRequest, ProbeRunResponse, ProbeRunner } from "./probe";

export function createNodeProbeRunner(): ProbeRunner {
  return (request: ProbeRunRequest): Promise<ProbeRunResponse> =>
    new Promise((resolve) => {
      let child;
      try {
        child = spawn(request.executable, [...request.args], {
          cwd: request.cwd,
          env: request.env,
          shell: false,
          windowsHide: true,
        });
      } catch (error) {
        const err = error as NodeJS.ErrnoException;
        resolve({
          exitCode: 1,
          stdout: "",
          stderr: "",
          timedOut: false,
          outputExceeded: false,
          spawnErrorCode: err.code ?? "SPAWN_ERROR",
        });
        return;
      }

      let stdout = "";
      let stderr = "";
      let outputExceeded = false;
      let timedOut = false;
      let settled = false;

      const finish = (exitCode: number, spawnErrorCode?: string): void => {
        if (settled) {
          return;
        }
        settled = true;
        clearTimeout(timer);
        resolve({
          exitCode,
          stdout,
          stderr,
          timedOut,
          outputExceeded,
          spawnErrorCode,
        });
      };

      const timer = setTimeout(() => {
        timedOut = true;
        try {
          child.kill("SIGKILL");
        } catch {
          // ignore
        }
        finish(1);
      }, request.timeoutMs);
      timer.unref?.();

      child.stdout?.on("data", (buf: Buffer) => {
        if (outputExceeded) {
          return;
        }
        stdout += buf.toString("utf8");
        if (Buffer.byteLength(stdout, "utf8") > request.maxStdoutBytes) {
          outputExceeded = true;
          try {
            child.kill("SIGKILL");
          } catch {
            // ignore
          }
        }
      });
      child.stderr?.on("data", (buf: Buffer) => {
        if (outputExceeded) {
          return;
        }
        stderr += buf.toString("utf8");
        if (Buffer.byteLength(stderr, "utf8") > request.maxStderrBytes) {
          outputExceeded = true;
          try {
            child.kill("SIGKILL");
          } catch {
            // ignore
          }
        }
      });
      child.on("error", (error: NodeJS.ErrnoException) => {
        finish(1, error.code ?? "SPAWN_ERROR");
      });
      child.on("close", (code) => {
        finish(code ?? 1);
      });
    });
}

/** Side-effect-free CLI version probe contract (Slice 13.2). */

import {
  DEFAULT_MAX_PROBE_STDERR_BYTES,
  DEFAULT_MAX_PROBE_STDOUT_BYTES,
  DEFAULT_PROBE_TIMEOUT_SECONDS,
} from "./policy";

/** Authoritative Engine metadata command — not assess/init/doctor. */
export const VERSION_PROBE_ARGS = ["version"] as const;

export type ProbeRunRequest = {
  readonly executable: string;
  readonly args: readonly string[];
  readonly cwd?: string;
  readonly timeoutMs: number;
  readonly maxStdoutBytes: number;
  readonly maxStderrBytes: number;
  readonly env?: NodeJS.ProcessEnv;
};

export type ProbeRunResponse = {
  readonly exitCode: number;
  readonly stdout: string;
  readonly stderr: string;
  readonly timedOut: boolean;
  readonly outputExceeded: boolean;
  readonly spawnErrorCode?: string;
};

export type ProbeRunner = (request: ProbeRunRequest) => Promise<ProbeRunResponse>;

export type ProbeLimits = {
  readonly timeoutSeconds: number;
  readonly maxStdoutBytes: number;
  readonly maxStderrBytes: number;
};

export function defaultProbeLimits(): ProbeLimits {
  return {
    timeoutSeconds: DEFAULT_PROBE_TIMEOUT_SECONDS,
    maxStdoutBytes: DEFAULT_MAX_PROBE_STDOUT_BYTES,
    maxStderrBytes: DEFAULT_MAX_PROBE_STDERR_BYTES,
  };
}

/**
 * Minimal environment for probes: inherit PATH/PATHEXT/SystemRoot only.
 * Does not mutate process.env; returns a bounded copy for spawn.
 */
export function buildProbeEnvironment(
  base: NodeJS.ProcessEnv = process.env
): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = {};
  for (const key of [
    "PATH",
    "Path",
    "PATHEXT",
    "SystemRoot",
    "SYSTEMROOT",
    "WINDIR",
    "HOME",
    "USERPROFILE",
    "LANG",
    "LC_ALL",
  ]) {
    if (base[key] !== undefined) {
      env[key] = base[key];
    }
  }
  // Force non-interactive metadata.
  env.CI = base.CI ?? "1";
  env.TERM = "dumb";
  return env;
}

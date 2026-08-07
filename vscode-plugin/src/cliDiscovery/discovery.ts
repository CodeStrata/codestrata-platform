/**
 * Authoritative CLI discovery orchestrator (Slice 13.2).
 *
 * Local-only, network-free, no installation. Version probe is separate from
 * product operation invocation.
 */

import { listDiscoveryCandidates, type DiscoveryCandidate } from "./candidates";
import { classifyDiscoveryCompatibility } from "./compatibility";
import { validateExplicitExecutable } from "./executableValidation";
import { parseProductIdentityOutput } from "./identity";
import {
  DEFAULT_DISCOVERY_LIMITATIONS,
  DEFAULT_MAX_CANDIDATES,
} from "./policy";
import {
  VERSION_PROBE_ARGS,
  buildProbeEnvironment,
  defaultProbeLimits,
  type ProbeLimits,
  type ProbeRunner,
} from "./probe";
import type {
  CliDiscoveryOutcome,
  CliDiscoveryResult,
  CliDiscoveryStatus,
  ResolvedCodeStrataCli,
} from "./results";
import type { CliCandidateSource } from "./sources";
import { formatSemanticVersion } from "./versions";

export type DiscoverCodeStrataCliInput = {
  readonly configuredExecutable: string;
  readonly workspaceFolders: readonly string[];
  readonly runner: ProbeRunner;
  readonly cwd?: string;
  readonly env?: NodeJS.ProcessEnv;
  readonly platform?: NodeJS.Platform;
  readonly limits?: ProbeLimits;
  readonly limitations?: readonly string[];
  readonly maxCandidates?: number;
};

function baseResult(
  partial: Partial<CliDiscoveryResult> &
    Pick<CliDiscoveryResult, "status" | "candidate_source">,
  limitations: readonly string[]
): CliDiscoveryResult {
  return {
    status: partial.status,
    candidate_source: partial.candidate_source,
    product_identity_valid: partial.product_identity_valid ?? false,
    version_present: partial.version_present ?? false,
    version_major: partial.version_major,
    version_minor: partial.version_minor,
    version_patch: partial.version_patch,
    compatibility_category: partial.compatibility_category ?? "not_applicable",
    executable_available: partial.executable_available ?? false,
    probe_attempted: partial.probe_attempted ?? false,
    probe_timed_out: partial.probe_timed_out ?? false,
    limitations: [...(partial.limitations ?? limitations)].sort(),
  };
}

function statusForValidation(
  status: string
): Extract<
  CliDiscoveryStatus,
  "not_found" | "not_executable" | "invalid_configuration"
> {
  if (status === "missing") {
    return "not_found";
  }
  if (status === "not_executable") {
    return "not_executable";
  }
  return "invalid_configuration";
}

async function probeCandidate(
  candidate: DiscoveryCandidate,
  input: DiscoverCodeStrataCliInput,
  limits: ProbeLimits,
  limitations: readonly string[]
): Promise<CliDiscoveryOutcome> {
  if (candidate.requiresFilesystemValidation) {
    const validation = validateExplicitExecutable(candidate.command, {
      platform: input.platform,
    });
    if (validation.status !== "ok") {
      return {
        public: baseResult(
          {
            status: statusForValidation(validation.status),
            candidate_source: candidate.source,
            executable_available: false,
            probe_attempted: false,
          },
          limitations
        ),
      };
    }
  }

  const response = await input.runner({
    executable: candidate.command,
    args: [...VERSION_PROBE_ARGS],
    cwd: input.cwd,
    timeoutMs: limits.timeoutSeconds * 1000,
    maxStdoutBytes: limits.maxStdoutBytes,
    maxStderrBytes: limits.maxStderrBytes,
    env: buildProbeEnvironment(input.env),
  });

  if (response.spawnErrorCode === "ENOENT") {
    return {
      public: baseResult(
        {
          status: "not_found",
          candidate_source: candidate.source,
          executable_available: false,
          probe_attempted: true,
        },
        limitations
      ),
    };
  }

  if (response.timedOut) {
    return {
      public: baseResult(
        {
          status: "probe_timed_out",
          candidate_source: candidate.source,
          executable_available: true,
          probe_attempted: true,
          probe_timed_out: true,
        },
        limitations
      ),
    };
  }

  if (response.outputExceeded) {
    return {
      public: baseResult(
        {
          status: "probe_failed",
          candidate_source: candidate.source,
          executable_available: true,
          probe_attempted: true,
        },
        limitations
      ),
    };
  }

  if (response.exitCode !== 0) {
    return {
      public: baseResult(
        {
          status: "probe_failed",
          candidate_source: candidate.source,
          executable_available: true,
          probe_attempted: true,
        },
        limitations
      ),
    };
  }

  const identity = parseProductIdentityOutput(response.stdout, {
    maxBytes: limits.maxStdoutBytes,
  });
  if (!identity.ok) {
    const status: CliDiscoveryStatus =
      identity.reason === "identity_mismatch"
        ? "identity_mismatch"
        : identity.reason === "malformed_version" ||
            identity.reason === "contradictory_versions"
          ? "malformed_version"
          : identity.reason === "empty_output"
            ? "version_unavailable"
            : "probe_failed";
    return {
      public: baseResult(
        {
          status,
          candidate_source: candidate.source,
          product_identity_valid: false,
          executable_available: true,
          probe_attempted: true,
        },
        limitations
      ),
    };
  }

  const compatibility = classifyDiscoveryCompatibility(identity.version);
  if (compatibility !== "compatible") {
    return {
      public: baseResult(
        {
          status: "incompatible",
          candidate_source: candidate.source,
          product_identity_valid: true,
          version_present: true,
          version_major: identity.version.major,
          version_minor: identity.version.minor,
          version_patch: identity.version.patch,
          compatibility_category: compatibility,
          executable_available: true,
          probe_attempted: true,
        },
        limitations
      ),
    };
  }

  const resolved: ResolvedCodeStrataCli = {
    command: candidate.command,
    source: candidate.source,
    version: formatSemanticVersion(identity.version),
    version_major: identity.version.major,
    version_minor: identity.version.minor,
    version_patch: identity.version.patch,
  };

  return {
    public: baseResult(
      {
        status: "compatible",
        candidate_source: candidate.source,
        product_identity_valid: true,
        version_present: true,
        version_major: identity.version.major,
        version_minor: identity.version.minor,
        version_patch: identity.version.patch,
        compatibility_category: "compatible",
        executable_available: true,
        probe_attempted: true,
      },
      limitations
    ),
    resolved,
  };
}

/**
 * Discover a compatible CodeStrata CLI.
 *
 * Explicit configuration fails closed (no PATH fallback).
 * Development and PATH candidates are tried in order until one is compatible.
 */
export async function discoverCodeStrataCli(
  input: DiscoverCodeStrataCliInput
): Promise<CliDiscoveryOutcome> {
  const limitations = input.limitations ?? DEFAULT_DISCOVERY_LIMITATIONS;
  const limits = input.limits ?? defaultProbeLimits();
  const candidates = listDiscoveryCandidates({
    configuredExecutable: input.configuredExecutable,
    workspaceFolders: input.workspaceFolders,
    env: input.env,
    platform: input.platform,
    maxCandidates: input.maxCandidates ?? DEFAULT_MAX_CANDIDATES,
  });

  if (candidates.length === 0) {
    return {
      public: baseResult(
        {
          status: "not_found",
          candidate_source: "unavailable",
          probe_attempted: false,
        },
        limitations
      ),
    };
  }

  const explicitOnly =
    candidates.length === 1 && candidates[0].source === "explicit_configuration";

  let lastOutcome: CliDiscoveryOutcome | undefined;

  for (const candidate of candidates) {
    const outcome = await probeCandidate(candidate, input, limits, limitations);
    lastOutcome = outcome;
    if (outcome.public.status === "compatible" && outcome.resolved) {
      return outcome;
    }
    if (explicitOnly) {
      // Fail closed — do not fall back to PATH.
      return outcome;
    }
    // Non-explicit: continue to next candidate on not_found / probe failures.
    if (
      outcome.public.status === "compatible" ||
      outcome.public.status === "incompatible" ||
      outcome.public.status === "identity_mismatch" ||
      outcome.public.status === "malformed_version"
    ) {
      // Found an executable that is wrong product/version — stop (do not
      // silently pick another binary after identity validation against a
      // development candidate that responded).
      if (
        candidate.source === "development_environment" &&
        (outcome.public.status === "incompatible" ||
          outcome.public.status === "identity_mismatch" ||
          outcome.public.status === "malformed_version")
      ) {
        return outcome;
      }
      if (outcome.public.status === "incompatible") {
        return outcome;
      }
    }
  }

  return (
    lastOutcome ?? {
      public: baseResult(
        {
          status: "not_found",
          candidate_source: "unavailable" as CliCandidateSource,
          probe_attempted: false,
        },
        limitations
      ),
    }
  );
}

/** Bounded local output-channel message (no paths). */
export function discoveryOutputMessage(result: CliDiscoveryResult): string {
  switch (result.status) {
    case "compatible":
      return `CodeStrata CLI detected (${result.candidate_source}; ${result.version_major}.${result.version_minor}.${result.version_patch}).`;
    case "not_found":
      return "CodeStrata CLI not found.";
    case "invalid_configuration":
    case "not_executable":
      return "Configured CodeStrata CLI unavailable.";
    case "incompatible":
      return "Unsupported CodeStrata CLI version.";
    case "identity_mismatch":
      return "CLI identity probe rejected non-CodeStrata executable.";
    case "probe_timed_out":
      return "CodeStrata CLI version probe timed out.";
    case "malformed_version":
    case "version_unavailable":
    case "probe_failed":
    default:
      return "CodeStrata CLI version probe failed.";
  }
}

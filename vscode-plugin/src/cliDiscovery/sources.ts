/** Closed CLI candidate-source vocabulary (Slice 13.2). */

export const CLI_CANDIDATE_SOURCES = [
  "explicit_configuration",
  "development_environment",
  "process_path",
  "unavailable",
] as const;

export type CliCandidateSource = (typeof CLI_CANDIDATE_SOURCES)[number];

export function isCliCandidateSource(value: string): value is CliCandidateSource {
  return (CLI_CANDIDATE_SOURCES as readonly string[]).includes(value);
}

/**
 * Precedence (after fail-closed explicit handling):
 * 1. explicit_configuration (invalid → fail closed, no fallback)
 * 2. development_environment (workspace .venv / active Python — existing contract)
 * 3. process_path
 * 4. unavailable
 */
export const CANDIDATE_SOURCE_PRECEDENCE: readonly CliCandidateSource[] = [
  "explicit_configuration",
  "development_environment",
  "process_path",
] as const;

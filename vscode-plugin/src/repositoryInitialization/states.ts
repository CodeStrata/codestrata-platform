/** Closed repository initialization-state vocabulary (Slice 13.4). */

export const REPOSITORY_INIT_STATES = [
  "not_initialized",
  "initialized",
  "invalid_configuration",
  "partial_initialization",
  "unknown",
] as const;

export type RepositoryInitState = (typeof REPOSITORY_INIT_STATES)[number];

export function isRepositoryInitState(
  value: string
): value is RepositoryInitState {
  return (REPOSITORY_INIT_STATES as readonly string[]).includes(value);
}

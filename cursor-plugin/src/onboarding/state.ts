/** Pure onboarding helpers (no vscode import — unit-testable). */

export function classifyEnginePresence(input: {
  found: boolean;
  compatible?: boolean;
}): "missing" | "incompatible" | "ready" {
  if (!input.found) {
    return "missing";
  }
  if (input.compatible === false) {
    return "incompatible";
  }
  return "ready";
}

export const SUPPORTED_CURSOR_EXTENSION_SERIES = "0.2.x";

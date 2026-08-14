/**
 * Engine telemetry consent CLI contract (Slice 20.10).
 *
 * VS Code must not re-implement consent_scope semantics. It only invokes:
 *   codestrata telemetry status --json
 *   codestrata telemetry enable
 *   codestrata telemetry disable
 *   codestrata telemetry decline-upgrade
 *
 * Decision: do NOT pass --telemetry-allow on assess. Durable V2_YES already
 * authorizes quiet/json-summary Engine sessions (Slice 20.9).
 */

export type EngineConsentState =
  | "undecided"
  | "v1_yes"
  | "v2_yes"
  | "disabled";

export type EngineConsentStatus = {
  readonly schemaVersion: "1";
  readonly state: EngineConsentState;
  readonly lifecycleAllowed: boolean;
  readonly assessmentMetadataAllowed: boolean;
  readonly shouldPromptV2Upgrade: boolean;
  readonly v2UpgradeDeclined: boolean;
};

export const TELEMETRY_STATUS_JSON_ARGS = [
  "telemetry",
  "status",
  "--json",
] as const;
export const TELEMETRY_ENABLE_ARGS = ["telemetry", "enable"] as const;
export const TELEMETRY_DISABLE_ARGS = ["telemetry", "disable"] as const;
export const TELEMETRY_DECLINE_UPGRADE_ARGS = [
  "telemetry",
  "decline-upgrade",
] as const;

const VALID_STATES = new Set<EngineConsentState>([
  "undecided",
  "v1_yes",
  "v2_yes",
  "disabled",
]);

/**
 * Parse `codestrata telemetry status --json` stdout.
 * Fail-closed on malformed / unrecognized payloads.
 */
export function parseEngineConsentStatusJson(
  stdout: string
): EngineConsentStatus | null {
  const text = stdout.trim();
  if (!text) {
    return null;
  }
  let parsed: unknown;
  try {
    // Prefer last JSON object when human noise precedes (should not happen with --json).
    const lines = text
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);
    const candidate =
      [...lines].reverse().find((line) => line.startsWith("{")) ?? text;
    parsed = JSON.parse(candidate);
  } catch {
    return null;
  }
  if (!parsed || typeof parsed !== "object") {
    return null;
  }
  const raw = parsed as Record<string, unknown>;
  const state = raw.state;
  if (typeof state !== "string" || !VALID_STATES.has(state as EngineConsentState)) {
    return null;
  }
  return {
    schemaVersion: "1",
    state: state as EngineConsentState,
    lifecycleAllowed: raw.lifecycle_allowed === true,
    assessmentMetadataAllowed: raw.assessment_metadata_allowed === true,
    shouldPromptV2Upgrade: raw.should_prompt_v2_upgrade === true,
    v2UpgradeDeclined: raw.v2_upgrade_declined === true,
  };
}

export type EngineConsentCommandResult = {
  readonly ok: boolean;
  readonly exitCode: number;
};

export type EngineConsentCliRunner = {
  run(
    args: readonly string[]
  ): Promise<{ exitCode: number; stdout: string; stderr: string }>;
};

export async function queryEngineConsentStatus(
  runner: EngineConsentCliRunner
): Promise<
  | { ok: true; status: EngineConsentStatus }
  | { ok: false; reason: "command_failed" | "malformed_status" }
> {
  let result: { exitCode: number; stdout: string; stderr: string };
  try {
    result = await runner.run(TELEMETRY_STATUS_JSON_ARGS);
  } catch {
    return { ok: false, reason: "command_failed" };
  }
  if (result.exitCode !== 0) {
    return { ok: false, reason: "command_failed" };
  }
  const status = parseEngineConsentStatusJson(result.stdout);
  if (!status) {
    return { ok: false, reason: "malformed_status" };
  }
  return { ok: true, status };
}

export async function runEngineTelemetryEnable(
  runner: EngineConsentCliRunner
): Promise<EngineConsentCommandResult> {
  try {
    const result = await runner.run(TELEMETRY_ENABLE_ARGS);
    return { ok: result.exitCode === 0, exitCode: result.exitCode };
  } catch {
    return { ok: false, exitCode: 1 };
  }
}

export async function runEngineTelemetryDisable(
  runner: EngineConsentCliRunner
): Promise<EngineConsentCommandResult> {
  try {
    const result = await runner.run(TELEMETRY_DISABLE_ARGS);
    return { ok: result.exitCode === 0, exitCode: result.exitCode };
  } catch {
    return { ok: false, exitCode: 1 };
  }
}

export async function runEngineTelemetryDeclineUpgrade(
  runner: EngineConsentCliRunner
): Promise<EngineConsentCommandResult> {
  try {
    const result = await runner.run(TELEMETRY_DECLINE_UPGRADE_ARGS);
    return { ok: result.exitCode === 0, exitCode: result.exitCode };
  } catch {
    return { ok: false, exitCode: 1 };
  }
}

/** Safe user-facing error — no paths, env, or command dumps. */
export function engineConsentFailureMessage(
  action: "enable" | "disable" | "decline-upgrade" | "status"
): string {
  if (action === "enable") {
    return (
      "Could not save Community telemetry preference. " +
      "Assessment continues locally without Community collection."
    );
  }
  if (action === "disable") {
    return (
      "Could not disable Community telemetry preference. " +
      "Check `codestrata telemetry status` from a terminal."
    );
  }
  if (action === "decline-upgrade") {
    return (
      "Could not update assessment-insights preference. " +
      "Existing lifecycle preference is unchanged."
    );
  }
  return (
    "Could not read Community telemetry status. " +
    "Assessment continues locally without Community collection."
  );
}

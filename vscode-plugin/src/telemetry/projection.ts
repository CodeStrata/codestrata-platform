/**
 * Privacy projection for VS Code telemetry events (Slice 9.13).
 */

import {
  APPROVED_EVENT_TYPES,
  VSCODE_CLIENT_NAME,
  eventToIntakeDict,
  type VsCodeRuntimeTelemetryEvent,
} from "./events";
import { looksLikeUnsafeValue } from "./privacy";
import {
  COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_VERSION,
  VSCODE_TELEMETRY_EVENT_SCHEMA_VERSION,
} from "./runtimePolicy";

export type PrivacySafeVsCodeTelemetryEvent = {
  readonly fields: Readonly<Record<string, unknown>>;
};

export class TelemetryProjectionError extends Error {
  readonly code: string;
  constructor(code: string) {
    super(code);
    this.code = code;
    this.name = "TelemetryProjectionError";
  }
}

const ENUM_FIELDS: Record<string, readonly string[]> = {
  event_type: APPROVED_EVENT_TYPES,
  os_family: ["linux", "macos", "windows", "other"],
  lifecycle: ["start", "complete", "fail"],
  result: ["success", "failure", "cancelled", "unknown"],
  duration_bucket: ["lt_1s", "s_1_10", "s_10_60", "m_1_5", "gt_5m"],
  operation_category: ["assess", "report", "other"],
};

export function projectRuntimeEvent(
  event: VsCodeRuntimeTelemetryEvent
): PrivacySafeVsCodeTelemetryEvent {
  const intake = eventToIntakeDict(event);
  const projected: Record<string, unknown> = {
    schema_version: VSCODE_TELEMETRY_EVENT_SCHEMA_VERSION,
    runtime_policy_version: COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_VERSION,
  };

  for (const [key, value] of Object.entries(intake)) {
    projected[key] = normalizeValue(key, value);
  }

  if (projected.client_name !== VSCODE_CLIENT_NAME) {
    throw new TelemetryProjectionError("unsafe_client");
  }
  if (typeof projected.event_type !== "string") {
    throw new TelemetryProjectionError("missing_event_type");
  }

  const sorted: Record<string, unknown> = {};
  for (const key of Object.keys(projected).sort()) {
    sorted[key] = projected[key];
  }
  return { fields: sorted };
}

function normalizeValue(key: string, value: unknown): unknown {
  if (key in ENUM_FIELDS) {
    if (typeof value !== "string" || !ENUM_FIELDS[key].includes(value)) {
      throw new TelemetryProjectionError("unsafe_value");
    }
    return value;
  }
  if (key === "offline_mode" || key === "ai_used") {
    if (typeof value !== "boolean") {
      throw new TelemetryProjectionError("unsafe_value");
    }
    return value;
  }
  if (key === "client_name" || key === "extension_version") {
    if (typeof value !== "string" || !value || value.length > 32) {
      throw new TelemetryProjectionError("unsafe_value");
    }
    if (looksLikeUnsafeValue(value) || value.includes("/") || value.includes("\\")) {
      throw new TelemetryProjectionError("unsafe_value");
    }
    if (key === "client_name" && value !== VSCODE_CLIENT_NAME) {
      throw new TelemetryProjectionError("unsafe_client");
    }
    return value;
  }
  throw new TelemetryProjectionError("unknown_field");
}

export function privacySafeToStableJson(
  event: PrivacySafeVsCodeTelemetryEvent
): string {
  return JSON.stringify(event.fields, Object.keys(event.fields).sort());
}

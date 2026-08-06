/**
 * Bounded VS Code telemetry event model (Slice 9.13).
 * Schema: community-vscode-telemetry-event-schema:1.0
 */

export const VSCODE_CLIENT_NAME = "vscode_extension" as const;

export type VsCodeRuntimeEventType =
  | "feature_invoked"
  | "feature_completed"
  | "operation_failed";

export type VsCodeLifecycle = "start" | "complete" | "fail";
export type VsCodeResultCategory = "success" | "failure" | "cancelled" | "unknown";
export type VsCodeOperationCategory = "assess" | "report" | "other";
export type VsCodeOsFamily = "linux" | "macos" | "windows" | "other";
export type VsCodeDurationBucket =
  | "lt_1s"
  | "s_1_10"
  | "s_10_60"
  | "m_1_5"
  | "gt_5m";

export const APPROVED_EVENT_TYPES: readonly VsCodeRuntimeEventType[] = [
  "feature_invoked",
  "feature_completed",
  "operation_failed",
];

export const APPROVED_FIELD_NAMES = [
  "event_type",
  "client_name",
  "extension_version",
  "os_family",
  "lifecycle",
  "result",
  "duration_bucket",
  "operation_category",
  "offline_mode",
  "ai_used",
  "schema_version",
  "runtime_policy_version",
] as const;

export type VsCodeRuntimeTelemetryEvent = {
  readonly eventType: VsCodeRuntimeEventType;
  readonly clientName: typeof VSCODE_CLIENT_NAME;
  readonly extensionVersion?: string;
  readonly osFamily?: VsCodeOsFamily;
  readonly lifecycle?: VsCodeLifecycle;
  readonly result?: VsCodeResultCategory;
  readonly durationBucket?: VsCodeDurationBucket;
  readonly operationCategory?: VsCodeOperationCategory;
  readonly offlineMode?: boolean;
  readonly aiUsed?: boolean;
};

export function createAssessInvokedEvent(options: {
  aiUsed: boolean;
  extensionVersion?: string;
}): VsCodeRuntimeTelemetryEvent {
  return {
    eventType: "feature_invoked",
    clientName: VSCODE_CLIENT_NAME,
    extensionVersion: options.extensionVersion,
    operationCategory: "assess",
    lifecycle: "start",
    aiUsed: options.aiUsed,
  };
}

export function createAssessCompletedEvent(options: {
  aiUsed: boolean;
  success: boolean;
  cancelled?: boolean;
  extensionVersion?: string;
  durationBucket?: VsCodeDurationBucket;
}): VsCodeRuntimeTelemetryEvent {
  if (options.cancelled) {
    return {
      eventType: "feature_completed",
      clientName: VSCODE_CLIENT_NAME,
      extensionVersion: options.extensionVersion,
      operationCategory: "assess",
      lifecycle: "complete",
      result: "cancelled",
      aiUsed: options.aiUsed,
      durationBucket: options.durationBucket,
    };
  }
  return {
    eventType: options.success ? "feature_completed" : "operation_failed",
    clientName: VSCODE_CLIENT_NAME,
    extensionVersion: options.extensionVersion,
    operationCategory: "assess",
    lifecycle: options.success ? "complete" : "fail",
    result: options.success ? "success" : "failure",
    aiUsed: options.aiUsed,
    durationBucket: options.durationBucket,
  };
}

export function eventToIntakeDict(
  event: VsCodeRuntimeTelemetryEvent
): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    client_name: event.clientName,
    event_type: event.eventType,
  };
  if (event.extensionVersion !== undefined) {
    payload.extension_version = event.extensionVersion;
  }
  if (event.osFamily !== undefined) {
    payload.os_family = event.osFamily;
  }
  if (event.lifecycle !== undefined) {
    payload.lifecycle = event.lifecycle;
  }
  if (event.result !== undefined) {
    payload.result = event.result;
  }
  if (event.durationBucket !== undefined) {
    payload.duration_bucket = event.durationBucket;
  }
  if (event.operationCategory !== undefined) {
    payload.operation_category = event.operationCategory;
  }
  if (event.offlineMode !== undefined) {
    payload.offline_mode = event.offlineMode;
  }
  if (event.aiUsed !== undefined) {
    payload.ai_used = event.aiUsed;
  }
  return payload;
}

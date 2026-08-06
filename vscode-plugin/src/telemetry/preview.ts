/**
 * Local preview for VS Code telemetry (Slice 9.13).
 * No transmission. No consent required. Deterministic.
 */

import {
  createAssessInvokedEvent,
  type VsCodeRuntimeTelemetryEvent,
} from "./events";
import {
  privacySafeToStableJson,
  projectRuntimeEvent,
  type PrivacySafeVsCodeTelemetryEvent,
} from "./projection";
import {
  COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_VERSION,
  VSCODE_TELEMETRY_EVENT_SCHEMA_VERSION,
} from "./runtimePolicy";

export type VsCodeTelemetryPreview = {
  readonly schemaVersion: string;
  readonly runtimePolicyVersion: string;
  readonly transmissionPerformed: false;
  readonly localOnly: true;
  readonly event: PrivacySafeVsCodeTelemetryEvent;
};

export function buildVsCodeTelemetryPreview(options?: {
  event?: VsCodeRuntimeTelemetryEvent;
  extensionVersion?: string;
}): VsCodeTelemetryPreview {
  const event =
    options?.event ??
    createAssessInvokedEvent({
      aiUsed: false,
      extensionVersion: options?.extensionVersion ?? "0.2.0",
    });
  const projected = projectRuntimeEvent(event);
  return {
    schemaVersion: VSCODE_TELEMETRY_EVENT_SCHEMA_VERSION,
    runtimePolicyVersion: COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_VERSION,
    transmissionPerformed: false,
    localOnly: true,
    event: projected,
  };
}

export function previewToStableJson(preview: VsCodeTelemetryPreview): string {
  const payload = {
    event: preview.event.fields,
    localOnly: preview.localOnly,
    runtimePolicyVersion: preview.runtimePolicyVersion,
    schemaVersion: preview.schemaVersion,
    transmissionPerformed: preview.transmissionPerformed,
  };
  return JSON.stringify(payload, Object.keys(payload).sort());
}

export function previewEventJson(preview: VsCodeTelemetryPreview): string {
  return privacySafeToStableJson(preview.event);
}

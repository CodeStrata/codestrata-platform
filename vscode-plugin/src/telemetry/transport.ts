/**
 * Telemetry transport port for VS Code (Slice 9.13).
 */

import type { PrivacySafeVsCodeTelemetryEvent } from "./projection";

export type TelemetryTransportResultKind =
  | "sent"
  | "disabled"
  | "unavailable"
  | "rejected"
  | "failed_silently";

export type TelemetryTransportResult = {
  readonly kind: TelemetryTransportResultKind;
};

export type ExtensionTelemetryTransport = {
  readonly transportCategory: string;
  send(event: PrivacySafeVsCodeTelemetryEvent): TelemetryTransportResult;
};

/**
 * Default unavailable VS Code telemetry transport (Slice 9.13).
 */

import type { PrivacySafeVsCodeTelemetryEvent } from "./projection";
import type {
  ExtensionTelemetryTransport,
  TelemetryTransportResult,
} from "./transport";

export class UnavailableExtensionTelemetryTransport
  implements ExtensionTelemetryTransport
{
  readonly transportCategory = "unavailable";

  send(_event: PrivacySafeVsCodeTelemetryEvent): TelemetryTransportResult {
    return { kind: "unavailable" };
  }
}

export function defaultUnavailableTransport(): UnavailableExtensionTelemetryTransport {
  return new UnavailableExtensionTelemetryTransport();
}

/**
 * Test-only capture transport (Slice 9.13).
 */

import type { PrivacySafeVsCodeTelemetryEvent } from "./projection";
import type {
  ExtensionTelemetryTransport,
  TelemetryTransportResult,
  TelemetryTransportResultKind,
} from "./transport";

export class CaptureExtensionTelemetryTransport
  implements ExtensionTelemetryTransport
{
  readonly transportCategory = "capture";
  readonly captured: PrivacySafeVsCodeTelemetryEvent[] = [];

  constructor(
    private readonly resultKind: TelemetryTransportResultKind = "sent",
    private readonly raiseOnSend = false
  ) {}

  send(event: PrivacySafeVsCodeTelemetryEvent): TelemetryTransportResult {
    if (this.raiseOnSend) {
      throw new Error("capture_transport_simulated_failure");
    }
    this.captured.push(event);
    return { kind: this.resultKind };
  }

  clear(): void {
    this.captured.length = 0;
  }
}

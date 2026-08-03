"""Internal telemetry diagnostics — never returned in API responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TelemetryIngestionDiagnostics:
    request_validated: bool
    identity_available: bool
    retry_status: str | None
    sink_status: str | None
    identity_record_status: str | None
    safe_event_reference: str | None
    telemetry_schema_version: str
    telemetry_policy_version: str
    limitations: tuple[str, ...] = ()

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "identity_available": self.identity_available,
            "limitations": list(self.limitations),
            "request_validated": self.request_validated,
            "telemetry_policy_version": self.telemetry_policy_version,
            "telemetry_schema_version": self.telemetry_schema_version,
        }
        if self.identity_record_status is not None:
            payload["identity_record_status"] = self.identity_record_status
        if self.retry_status is not None:
            payload["retry_status"] = self.retry_status
        if self.safe_event_reference is not None:
            payload["safe_event_reference"] = self.safe_event_reference
        if self.sink_status is not None:
            payload["sink_status"] = self.sink_status
        return {key: payload[key] for key in sorted(payload)}

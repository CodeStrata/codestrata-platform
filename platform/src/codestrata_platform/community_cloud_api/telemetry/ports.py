"""Telemetry sink ports — persistence-neutral (Slice 7.7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from codestrata_platform.community_cloud_api.telemetry.enums import TelemetrySinkStatus
from codestrata_platform.community_cloud_api.telemetry.models import (
    TelemetryClient,
    TelemetryProperties,
)


@dataclass(frozen=True, slots=True)
class ValidatedTelemetryEvent:
    """Sink-facing event — no raw event_id, installation_id, or request body."""

    event_key: str
    safe_event_reference: str
    schema_version: str
    event_type: str
    client: TelemetryClient
    occurred_at: str | None
    properties: TelemetryProperties | None
    payload_fingerprint: str
    identity_policy_version: str
    telemetry_policy_version: str

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "client": self.client.to_stable_dict(),
            "event_key": self.event_key,
            "event_type": self.event_type,
            "identity_policy_version": self.identity_policy_version,
            "payload_fingerprint": self.payload_fingerprint,
            "safe_event_reference": self.safe_event_reference,
            "schema_version": self.schema_version,
            "telemetry_policy_version": self.telemetry_policy_version,
        }
        if self.occurred_at is not None:
            payload["occurred_at"] = self.occurred_at
        if self.properties is not None:
            payload["properties"] = self.properties.to_stable_dict()
        return {key: payload[key] for key in sorted(payload)}


@dataclass(frozen=True, slots=True)
class TelemetrySinkResult:
    status: TelemetrySinkStatus
    reason: str = ""

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"status": self.status.value}
        if self.reason:
            payload["reason"] = self.reason
        return {key: payload[key] for key in sorted(payload)}


class TelemetryEventSink(Protocol):
    def accept(self, event: ValidatedTelemetryEvent) -> TelemetrySinkResult: ...


class UnavailableTelemetryEventSink:
    """Default production sink — never claims durable acceptance."""

    def accept(self, event: ValidatedTelemetryEvent) -> TelemetrySinkResult:
        _ = event
        return TelemetrySinkResult(
            status=TelemetrySinkStatus.UNAVAILABLE,
            reason="telemetry_sink_unavailable",
        )


# Alias used in docs / wiring.
NullTelemetryEventSink = UnavailableTelemetryEventSink


@dataclass
class InMemoryTelemetryEventSink:
    """Test-only accepting sink — not a production adapter."""

    events: list[ValidatedTelemetryEvent] = field(default_factory=list)
    fail_next: bool = False
    reject_next: bool = False

    def accept(self, event: ValidatedTelemetryEvent) -> TelemetrySinkResult:
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("simulated_sink_failure")
        if self.reject_next:
            self.reject_next = False
            return TelemetrySinkResult(
                status=TelemetrySinkStatus.REJECTED,
                reason="telemetry_rejected",
            )
        self.events.append(event)
        return TelemetrySinkResult(status=TelemetrySinkStatus.ACCEPTED, reason="accepted")

    def clear(self) -> None:
        self.events.clear()

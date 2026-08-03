"""Extension event sink ports — persistence-neutral (Slice 7.10)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from codestrata_platform.community_cloud_api.extension_events.enums import (
    ExtensionEventSinkStatus,
)
from codestrata_platform.community_cloud_api.extension_events.models import (
    ExtensionClient,
    ExtensionEventContext,
)


@dataclass(frozen=True, slots=True)
class ValidatedExtensionEvent:
    """Sink-facing event — no raw event_id, installation_id, or workspace identity."""

    event_key: str
    safe_event_reference: str
    schema_version: str
    client: ExtensionClient
    operation: str
    lifecycle: str
    result: str
    duration_bucket: str
    failure_category: str | None
    context: ExtensionEventContext
    identity_policy_version: str
    extension_event_policy_version: str
    operation_catalog_version: str

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "client": self.client.to_stable_dict(),
            "context": self.context.to_stable_dict(),
            "duration_bucket": self.duration_bucket,
            "event_key": self.event_key,
            "extension_event_policy_version": self.extension_event_policy_version,
            "identity_policy_version": self.identity_policy_version,
            "lifecycle": self.lifecycle,
            "operation": self.operation,
            "operation_catalog_version": self.operation_catalog_version,
            "result": self.result,
            "safe_event_reference": self.safe_event_reference,
            "schema_version": self.schema_version,
        }
        if self.failure_category is not None:
            payload["failure_category"] = self.failure_category
        return {key: payload[key] for key in sorted(payload)}


@dataclass(frozen=True, slots=True)
class ExtensionEventSinkResult:
    status: ExtensionEventSinkStatus
    reason: str = ""

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"status": self.status.value}
        if self.reason:
            payload["reason"] = self.reason
        return {key: payload[key] for key in sorted(payload)}


class ExtensionEventSink(Protocol):
    def accept(self, event: ValidatedExtensionEvent) -> ExtensionEventSinkResult: ...


class UnavailableExtensionEventSink:
    def accept(self, event: ValidatedExtensionEvent) -> ExtensionEventSinkResult:
        _ = event
        return ExtensionEventSinkResult(
            status=ExtensionEventSinkStatus.UNAVAILABLE,
            reason="extension_event_sink_unavailable",
        )


@dataclass
class InMemoryExtensionEventSink:
    events: list[ValidatedExtensionEvent] = field(default_factory=list)
    fail_next: bool = False
    reject_next: bool = False

    def accept(self, event: ValidatedExtensionEvent) -> ExtensionEventSinkResult:
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("simulated_extension_sink_failure")
        if self.reject_next:
            self.reject_next = False
            return ExtensionEventSinkResult(
                status=ExtensionEventSinkStatus.REJECTED,
                reason="extension_event_rejected",
            )
        self.events.append(event)
        return ExtensionEventSinkResult(
            status=ExtensionEventSinkStatus.ACCEPTED, reason="accepted"
        )

    def clear(self) -> None:
        self.events.clear()

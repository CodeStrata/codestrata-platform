"""CLI event sink ports — persistence-neutral (Slice 7.9)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from codestrata_platform.community_cloud_api.cli_events.enums import CliEventSinkStatus
from codestrata_platform.community_cloud_api.cli_events.models import CliClient, CliEventContext


@dataclass(frozen=True, slots=True)
class ValidatedCliEvent:
    """Sink-facing event — no raw event_id, installation_id, or command text."""

    event_key: str
    safe_event_reference: str
    schema_version: str
    operation: str
    lifecycle: str
    result: str
    duration_bucket: str
    failure_category: str | None
    context: CliEventContext
    client: CliClient
    identity_policy_version: str
    cli_event_policy_version: str
    operation_catalog_version: str

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "cli_event_policy_version": self.cli_event_policy_version,
            "client": self.client.to_stable_dict(),
            "context": self.context.to_stable_dict(),
            "duration_bucket": self.duration_bucket,
            "event_key": self.event_key,
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
class CliEventSinkResult:
    status: CliEventSinkStatus
    reason: str = ""

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"status": self.status.value}
        if self.reason:
            payload["reason"] = self.reason
        return {key: payload[key] for key in sorted(payload)}


class CliEventSink(Protocol):
    def accept(
        self,
        event: ValidatedCliEvent,
        *,
        request: Any | None = None,
    ) -> CliEventSinkResult: ...


class UnavailableCliEventSink:
    def accept(
        self,
        event: ValidatedCliEvent,
        *,
        request: Any | None = None,
    ) -> CliEventSinkResult:
        _ = event
        _ = request
        return CliEventSinkResult(
            status=CliEventSinkStatus.UNAVAILABLE,
            reason="cli_event_sink_unavailable",
        )


@dataclass
class InMemoryCliEventSink:
    events: list[ValidatedCliEvent] = field(default_factory=list)
    fail_next: bool = False
    reject_next: bool = False

    def accept(
        self,
        event: ValidatedCliEvent,
        *,
        request: Any | None = None,
    ) -> CliEventSinkResult:
        _ = request
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("simulated_cli_sink_failure")
        if self.reject_next:
            self.reject_next = False
            return CliEventSinkResult(
                status=CliEventSinkStatus.REJECTED, reason="cli_event_rejected"
            )
        self.events.append(event)
        return CliEventSinkResult(status=CliEventSinkStatus.ACCEPTED, reason="accepted")

    def clear(self) -> None:
        self.events.clear()

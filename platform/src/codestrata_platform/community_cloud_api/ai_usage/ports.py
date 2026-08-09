"""AI usage sink ports — persistence-neutral (Slice 7.11)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from codestrata_platform.community_cloud_api.ai_usage.enums import AiUsageSinkStatus
from codestrata_platform.community_cloud_api.ai_usage.models import (
    AiUsage,
    AiUsageClient,
    AiUsageContext,
)


@dataclass(frozen=True, slots=True)
class ValidatedAiUsageEvent:
    """Sink-facing event — no prompts, credentials, exact tokens, or raw IDs."""

    event_key: str
    safe_event_reference: str
    schema_version: str
    client: AiUsageClient
    usage: AiUsage
    context: AiUsageContext
    identity_policy_version: str
    ai_usage_policy_version: str
    capability_catalog_version: str
    provider_catalog_version: str
    model_catalog_version: str

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "ai_usage_policy_version": self.ai_usage_policy_version,
            "capability_catalog_version": self.capability_catalog_version,
            "client": self.client.to_stable_dict(),
            "context": self.context.to_stable_dict(),
            "event_key": self.event_key,
            "identity_policy_version": self.identity_policy_version,
            "model_catalog_version": self.model_catalog_version,
            "provider_catalog_version": self.provider_catalog_version,
            "safe_event_reference": self.safe_event_reference,
            "schema_version": self.schema_version,
            "usage": self.usage.to_stable_dict(),
        }


@dataclass(frozen=True, slots=True)
class AiUsageSinkResult:
    status: AiUsageSinkStatus
    reason: str = ""

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"status": self.status.value}
        if self.reason:
            payload["reason"] = self.reason
        return {key: payload[key] for key in sorted(payload)}


class AiUsageSink(Protocol):
    def accept(
        self,
        event: ValidatedAiUsageEvent,
        *,
        request: Any | None = None,
    ) -> AiUsageSinkResult: ...


class UnavailableAiUsageSink:
    def accept(
        self,
        event: ValidatedAiUsageEvent,
        *,
        request: Any | None = None,
    ) -> AiUsageSinkResult:
        _ = event
        _ = request
        return AiUsageSinkResult(
            status=AiUsageSinkStatus.UNAVAILABLE,
            reason="ai_usage_sink_unavailable",
        )


@dataclass
class InMemoryAiUsageSink:
    events: list[ValidatedAiUsageEvent] = field(default_factory=list)
    fail_next: bool = False
    reject_next: bool = False

    def accept(
        self,
        event: ValidatedAiUsageEvent,
        *,
        request: Any | None = None,
    ) -> AiUsageSinkResult:
        _ = request
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("simulated_ai_usage_sink_failure")
        if self.reject_next:
            self.reject_next = False
            return AiUsageSinkResult(
                status=AiUsageSinkStatus.REJECTED, reason="ai_usage_rejected"
            )
        self.events.append(event)
        return AiUsageSinkResult(status=AiUsageSinkStatus.ACCEPTED, reason="accepted")

    def clear(self) -> None:
        self.events.clear()

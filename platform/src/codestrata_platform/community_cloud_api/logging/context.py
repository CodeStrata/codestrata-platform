"""Per-request logging context (safe metadata only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from codestrata_platform.community_cloud_api.logging.models import CommunityLoggingPolicy
from codestrata_platform.community_cloud_api.logging.sanitization import (
    sanitize_client_host,
    sanitize_method,
    sanitize_request_id,
    sanitize_route,
)

ClockMs = Callable[[], int]
RequestIdFactory = Callable[[], str]


@dataclass(frozen=True, slots=True)
class LoggingContext:
    """Request-scoped logging identity — never written into response bodies."""

    request_id: str
    api_version: str
    method: str
    route: str
    started_ms: int
    client_host: str | None = None
    route_name: str | None = None
    correlation_id: str | None = None

    def with_route_name(self, route_name: str | None) -> LoggingContext:
        return LoggingContext(
            request_id=self.request_id,
            api_version=self.api_version,
            method=self.method,
            route=self.route,
            started_ms=self.started_ms,
            client_host=self.client_host,
            route_name=route_name,
            correlation_id=self.correlation_id,
        )


def create_logging_context(
    *,
    policy: CommunityLoggingPolicy,
    api_version: str,
    method: str,
    route: str,
    client_request_id: str | None,
    clock_ms: ClockMs,
    request_id_factory: RequestIdFactory,
    client_host: str | None = None,
) -> LoggingContext:
    """Build logging context. Auto-generated IDs stay logging-only."""

    sanitized = sanitize_request_id(
        client_request_id, max_length=policy.max_request_id_length
    )
    request_id = sanitized or request_id_factory()
    host = None
    if policy.include_client_host:
        host = sanitize_client_host(client_host, max_length=policy.max_field_length)
    return LoggingContext(
        request_id=request_id,
        api_version=(api_version or "").strip() or "v1",
        method=sanitize_method(method),
        route=sanitize_route(route, max_length=policy.max_field_length),
        started_ms=int(clock_ms()),
        client_host=host,
    )


class SequenceRequestIdFactory:
    """Deterministic request-id factory for tests and stable local runs."""

    def __init__(self, *, prefix: str = "req") -> None:
        self._prefix = prefix
        self._n = 0

    def __call__(self) -> str:
        self._n += 1
        return f"{self._prefix}-{self._n:08d}"


class SequenceClock:
    """Injectable clock returning deterministic millisecond counters."""

    def __init__(self, *, start_ms: int = 0, step_ms: int = 1) -> None:
        self._value = int(start_ms)
        self._step = int(step_ms)

    def __call__(self) -> int:
        current = self._value
        self._value += self._step
        return current

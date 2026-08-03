"""Helpers for Community Cloud rate-limit tests."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.event_identity import InMemoryEventIdentityStore
from codestrata_platform.community_cloud_api.logging.context import SequenceClock
from codestrata_platform.community_cloud_api.logging.logger import (
    CommunityCloudLogger,
    MemoryLogSink,
)
from codestrata_platform.community_cloud_api.rate_limiting import (
    CommunityRateLimitPolicy,
    InMemoryRateLimitStore,
    UnavailableRateLimitStore,
)
from codestrata_platform.community_cloud_api.rate_limiting.models import (
    RATE_LIMIT_GROUP_HEALTH,
    RATE_LIMIT_GROUP_INGESTION,
    RouteRateLimit,
)
from codestrata_platform.community_cloud_api.telemetry.ports import InMemoryTelemetryEventSink
from fastapi.testclient import TestClient


def tight_rate_limit_policy(
    *,
    health_limit: int = 2,
    ingestion_limit: int = 2,
    window_seconds: int = 60,
    enabled: bool = True,
) -> CommunityRateLimitPolicy:
    routes = (
        RouteRateLimit(
            route_id="health.get",
            group=RATE_LIMIT_GROUP_HEALTH,
            max_requests=health_limit,
            window_seconds=window_seconds,
        ),
        *(
            RouteRateLimit(
                route_id=route_id,
                group=RATE_LIMIT_GROUP_INGESTION,
                max_requests=ingestion_limit,
                window_seconds=window_seconds,
            )
            for route_id in (
                "telemetry.ingest",
                "assessment_metadata.ingest",
                "cli_events.ingest",
                "extension_events.ingest",
                "ai_usage.ingest",
            )
        ),
    )
    return CommunityRateLimitPolicy(
        enabled=enabled,
        route_limits=routes,
        default_limit=ingestion_limit,
        health_limit=health_limit,
        ingestion_limit=ingestion_limit,
        window_seconds=window_seconds,
        burst_capacity=max(ingestion_limit, health_limit),
        max_retry_after_seconds=window_seconds,
    )


def rate_limited_client(
    *,
    policy: CommunityRateLimitPolicy | None = None,
    store: object | None = None,
    clock: SequenceClock | None = None,
    unavailable_store: bool = False,
) -> tuple[TestClient, InMemoryTelemetryEventSink, InMemoryEventIdentityStore, MemoryLogSink, object]:
    identity = InMemoryEventIdentityStore()
    sink = InMemoryTelemetryEventSink()
    log_sink = MemoryLogSink()
    logger = CommunityCloudLogger.create(sink=log_sink)
    active_store: object
    if unavailable_store:
        active_store = UnavailableRateLimitStore()
    elif store is not None:
        active_store = store
    else:
        active_store = InMemoryRateLimitStore()
    clock_ms = clock or SequenceClock(start_ms=0, step_ms=0)
    app = create_community_cloud_app(
        telemetry_sink=sink,
        event_identity_lookup=identity,
        event_identity_recorder=identity,
        logger=logger,
        rate_limit_policy=policy or tight_rate_limit_policy(),
        rate_limit_store=active_store,  # type: ignore[arg-type]
        rate_limit_clock_ms=clock_ms,
            authentication_policy=disabled_authentication_policy(),
    )
    return TestClient(app), sink, identity, log_sink, active_store

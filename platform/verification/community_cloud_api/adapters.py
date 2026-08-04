"""In-memory adapters and spy wrappers for SV.7."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from codestrata_platform.community_cloud_api.rate_limiting import CommunityRateLimitPolicy
from codestrata_platform.community_cloud_api.rate_limiting.models import (
    RATE_LIMIT_GROUP_HEALTH,
    RATE_LIMIT_GROUP_INGESTION,
    RouteRateLimit,
)


@dataclass
class SpyCounter:
    calls: list[str] = field(default_factory=list)

    def record(self, name: str) -> None:
        self.calls.append(name)

    def count(self, name: str) -> int:
        return sum(1 for item in self.calls if item == name)


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


def redact_for_diagnostics(value: Any) -> str:
    """Never include credentials or raw IDs in failure diagnostics."""

    text = str(value)
    for marker in ("cscc_v1_", "Bearer ", "Authorization"):
        if marker in text:
            return "<redacted>"
    if len(text) > 120:
        return text[:117] + "..."
    return text

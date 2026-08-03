"""Rate-limit policy unit tests."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.rate_limiting import (
    COMMUNITY_RATE_LIMIT_POLICY_URN,
    CommunityRateLimitPolicy,
    PRODUCTION_ROUTE_IDS,
)
from codestrata_platform.community_cloud_api.rate_limiting.models import (
    RouteRateLimit,
)
from codestrata_platform.community_cloud_api.registry import RouteRegistry

from .rate_limit_helpers import tight_rate_limit_policy


def test_stable_policy_token_and_version() -> None:
    policy = CommunityRateLimitPolicy.default()
    assert policy.policy_version == COMMUNITY_RATE_LIMIT_POLICY_URN
    assert policy.policy_token() == COMMUNITY_RATE_LIMIT_POLICY_URN
    assert policy.policy_token() == CommunityRateLimitPolicy.default().policy_token()
    assert COMMUNITY_RATE_LIMIT_POLICY_URN.endswith(":1.1")


def test_health_and_ingestion_policies() -> None:
    policy = CommunityRateLimitPolicy.default()
    health = policy.limit_for_route("health.get")
    assert health.group == "health"
    assert health.max_requests == 120
    assert health.window_seconds == 60
    for route_id in PRODUCTION_ROUTE_IDS:
        if route_id == "health.get":
            continue
        item = policy.limit_for_route(route_id)
        assert item.group == "ingestion"
        assert item.max_requests == 30


def test_every_production_route_covered() -> None:
    policy = CommunityRateLimitPolicy.default()
    covered = {item.route_id for item in policy.route_limits}
    assert covered == set(PRODUCTION_ROUTE_IDS)
    registry = RouteRegistry.foundation_v1()
    assert {r.name for r in registry.list_routes()} == set(PRODUCTION_ROUTE_IDS)


def test_invalid_zero_negative_and_window_rejected() -> None:
    with pytest.raises(ValueError):
        tight_rate_limit_policy(health_limit=0)
    with pytest.raises(ValueError):
        tight_rate_limit_policy(ingestion_limit=-1)
    with pytest.raises(ValueError):
        tight_rate_limit_policy(window_seconds=0)


def test_missing_and_unknown_route_policy_rejected() -> None:
    with pytest.raises(ValueError, match="missing"):
        CommunityRateLimitPolicy(
            route_limits=(
                RouteRateLimit(
                    route_id="health.get",
                    group="health",
                    max_requests=10,
                    window_seconds=60,
                ),
            ),
            health_limit=10,
            ingestion_limit=10,
            burst_capacity=10,
        )
    with pytest.raises(ValueError, match="unknown"):
        limits = list(CommunityRateLimitPolicy.default().route_limits) + [
            RouteRateLimit(
                route_id="mystery.route",
                group="ingestion",
                max_requests=1,
                window_seconds=60,
            )
        ]
        CommunityRateLimitPolicy(
            route_limits=tuple(limits),
            health_limit=120,
            ingestion_limit=30,
            burst_capacity=30,
        )


def test_deterministic_serialization() -> None:
    left = CommunityRateLimitPolicy.default().to_stable_dict()
    right = CommunityRateLimitPolicy.default().to_stable_dict()
    assert left == right
    assert list(left.keys()) == sorted(left.keys())

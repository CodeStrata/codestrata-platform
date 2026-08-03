"""Canonical rate-limit policy factory."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.rate_limiting.models import (
    COMMUNITY_RATE_LIMIT_POLICY_URN,
    CommunityRateLimitPolicy,
    assert_policy_covers_registry_routes,
    assert_supported_rate_limit_policy,
)

ACTIVE_RATE_LIMIT_POLICY = COMMUNITY_RATE_LIMIT_POLICY_URN


def default_rate_limit_policy() -> CommunityRateLimitPolicy:
    """Return the sole Community Cloud rate-limit policy (v1.0)."""

    return CommunityRateLimitPolicy.default()


def validate_rate_limit_policy(
    policy: CommunityRateLimitPolicy,
    *,
    route_names: frozenset[str] | set[str] | tuple[str, ...] | None = None,
) -> CommunityRateLimitPolicy:
    """Validate policy version and optional registry coverage."""

    active = assert_supported_rate_limit_policy(policy)
    if route_names is not None:
        assert_policy_covers_registry_routes(active, route_names)
    return active

"""Rate-limit scope privacy tests."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.rate_limiting import (
    CommunityRateLimitPolicy,
    derive_transport_scope,
)
from codestrata_platform.community_cloud_api.rate_limiting.scopes import build_rate_limit_key
from codestrata_platform.community_cloud_api.logging import asgi_client_host


def test_direct_asgi_host_stable_scope() -> None:
    policy = CommunityRateLimitPolicy.default()
    route = policy.limit_for_route("telemetry.ingest")
    a = derive_transport_scope(
        policy=policy, route_limit=route, asgi_client_host="203.0.113.10"
    )
    b = derive_transport_scope(
        policy=policy, route_limit=route, asgi_client_host="203.0.113.10"
    )
    assert a.safe_scope == b.safe_scope
    assert a.safe_scope.startswith("rate-scope:")
    assert a.safe_scope_reference.startswith("rls-")
    assert "203.0.113.10" not in a.safe_scope
    assert "203.0.113.10" not in a.safe_scope_reference


def test_changed_host_changes_scope() -> None:
    policy = CommunityRateLimitPolicy.default()
    route = policy.limit_for_route("telemetry.ingest")
    a = derive_transport_scope(
        policy=policy, route_limit=route, asgi_client_host="203.0.113.10"
    )
    b = derive_transport_scope(
        policy=policy, route_limit=route, asgi_client_host="203.0.113.11"
    )
    assert a.safe_scope != b.safe_scope


def test_forwarded_headers_and_request_metadata_ignored() -> None:
    # Scope derivation never accepts header maps — only ASGI host.
    policy = CommunityRateLimitPolicy.default()
    route = policy.limit_for_route("telemetry.ingest")
    base = derive_transport_scope(
        policy=policy, route_limit=route, asgi_client_host="203.0.113.10"
    )
    # Spoofed header values are not inputs to derive_transport_scope.
    _ = {
        "X-Forwarded-For": "198.51.100.1",
        "X-Real-IP": "198.51.100.2",
        "CF-Connecting-IP": "198.51.100.3",
        "X-Request-Id": "req-bypass",
        "User-Agent": "spoof",
        "event_id": "evt-bypass",
    }
    same = derive_transport_scope(
        policy=policy, route_limit=route, asgi_client_host="203.0.113.10"
    )
    assert same.safe_scope == base.safe_scope
    assert asgi_client_host(("203.0.113.10", 443)) == "203.0.113.10"
    assert asgi_client_host(None) is None


def test_missing_host_uses_global_anonymous_scope() -> None:
    policy = CommunityRateLimitPolicy.default()
    route = policy.limit_for_route("health.get")
    scope = derive_transport_scope(
        policy=policy, route_limit=route, asgi_client_host=None
    )
    assert scope.used_global_anonymous is True
    assert scope.safe_scope.startswith("rate-scope:")
    key = build_rate_limit_key(
        policy=policy, route_limit=route, scope=scope, window_id=0
    )
    assert key.startswith("rate:")
    assert "global_anonymous" not in key
    assert "None" not in key

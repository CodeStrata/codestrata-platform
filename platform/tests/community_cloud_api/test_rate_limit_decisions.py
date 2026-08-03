"""Fixed-window rate-limit algorithm and decision tests."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.rate_limiting import (
    CommunityRateLimitPolicy,
    InMemoryRateLimitStore,
    UnavailableRateLimitStore,
)
from codestrata_platform.community_cloud_api.rate_limiting.decisions import (
    DECISION_ALLOWED,
    DECISION_LIMITED,
    DECISION_UNAVAILABLE,
)
from codestrata_platform.community_cloud_api.rate_limiting.scopes import (
    build_rate_limit_key,
    derive_transport_scope,
)


def _eval(*, host: str, route_id: str, now_ms: int, store: InMemoryRateLimitStore):
    policy = CommunityRateLimitPolicy.default()
    # Use tight limits via route override by constructing store eval with custom limit
    from codestrata_platform.community_cloud_api.rate_limiting.models import RouteRateLimit

    route = RouteRateLimit(
        route_id=route_id,
        group="health" if route_id == "health.get" else "ingestion",
        max_requests=2,
        window_seconds=60,
    )
    scope = derive_transport_scope(
        policy=policy, route_limit=route, asgi_client_host=host
    )
    key = build_rate_limit_key(
        policy=policy,
        route_limit=route,
        scope=scope,
        window_id=now_ms // 60_000,
    )
    return store.evaluate(
        key,
        route_limit=route,
        now_ms=now_ms,
        max_retry_after_seconds=60,
        safe_scope_reference=scope.safe_scope_reference,
        policy_id=policy.policy_id,
    ), key, scope


def test_fixed_window_allow_limit_and_remaining() -> None:
    store = InMemoryRateLimitStore()
    first, key, _ = _eval(host="203.0.113.10", route_id="telemetry.ingest", now_ms=1000, store=store)
    assert first.status == DECISION_ALLOWED
    assert first.remaining == 1
    second, _, _ = _eval(host="203.0.113.10", route_id="telemetry.ingest", now_ms=2000, store=store)
    assert second.status == DECISION_ALLOWED
    assert second.remaining == 0
    third, _, _ = _eval(host="203.0.113.10", route_id="telemetry.ingest", now_ms=3000, store=store)
    assert third.status == DECISION_LIMITED
    assert third.remaining == 0
    assert third.retry_after_seconds is not None and third.retry_after_seconds >= 1
    assert "203.0.113.10" not in key


def test_reset_after_window_and_separate_buckets() -> None:
    store = InMemoryRateLimitStore()
    _eval(host="203.0.113.10", route_id="telemetry.ingest", now_ms=1000, store=store)
    _eval(host="203.0.113.10", route_id="telemetry.ingest", now_ms=2000, store=store)
    limited, _, _ = _eval(
        host="203.0.113.10", route_id="telemetry.ingest", now_ms=3000, store=store
    )
    assert limited.status == DECISION_LIMITED
    reset, _, _ = _eval(
        host="203.0.113.10", route_id="telemetry.ingest", now_ms=60_000, store=store
    )
    assert reset.status == DECISION_ALLOWED

    other_route, _, _ = _eval(
        host="203.0.113.10", route_id="health.get", now_ms=3000, store=store
    )
    assert other_route.status == DECISION_ALLOWED
    other_host, _, _ = _eval(
        host="203.0.113.99", route_id="telemetry.ingest", now_ms=3000, store=store
    )
    assert other_host.status == DECISION_ALLOWED


def test_unavailable_store_and_no_raw_host_keys() -> None:
    store = UnavailableRateLimitStore()
    policy = CommunityRateLimitPolicy.default()
    route = policy.limit_for_route("telemetry.ingest")
    scope = derive_transport_scope(
        policy=policy, route_limit=route, asgi_client_host="203.0.113.10"
    )
    decision = store.evaluate(
        "rate:deadbeefdeadbeefdeadbeef",
        route_limit=route,
        now_ms=0,
        max_retry_after_seconds=60,
        safe_scope_reference=scope.safe_scope_reference,
        policy_id=policy.policy_id,
    )
    assert decision.status == DECISION_UNAVAILABLE
    assert decision.allowed is False

    mem = InMemoryRateLimitStore()
    _eval(host="198.51.100.7", route_id="cli_events.ingest", now_ms=0, store=mem)
    for key in mem.key_snapshot():
        assert "198.51.100.7" not in key
        assert key.startswith("rate:")

"""Fixed-window in-memory rate-limit store and clock helpers."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from codestrata_platform.community_cloud_api.rate_limiting.decisions import (
    RateLimitDecision,
)
from codestrata_platform.community_cloud_api.rate_limiting.models import RouteRateLimit
from codestrata_platform.community_cloud_api.rate_limiting.scopes import build_rate_limit_key


ClockMs = Callable[[], int]


def monotonic_clock_ms() -> int:
    """Production default: monotonic milliseconds (not wall-clock identity)."""

    return int(time.monotonic() * 1000)


@dataclass
class _WindowBucket:
    window_id: int
    count: int = 0


@dataclass
class InMemoryRateLimitStore:
    """Process-local fixed-window store for tests and explicit local construction.

    Not suitable for distributed/serverless multi-instance enforcement.
    Keys contain only hashed scope material — never raw client hosts.
    """

    _buckets: dict[str, _WindowBucket] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    limitations: tuple[str, ...] = (
        "process_local",
        "not_distributed",
        "in_memory_only",
    )

    def evaluate(
        self,
        key: str,
        *,
        route_limit: RouteRateLimit,
        now_ms: int,
        max_retry_after_seconds: int,
        safe_scope_reference: str,
        policy_id: str,
        limitations: tuple[str, ...] = (),
    ) -> RateLimitDecision:
        if not key.startswith("rate:"):
            raise ValueError("rate-limit key must be a hashed rate: prefix key")
        if any(ch.isspace() for ch in key):
            raise ValueError("rate-limit key must not contain whitespace")
        # Reject accidental raw-host embedding heuristics for tests/privacy.
        if ":" in key[5:] and any(
            token in key.lower()
            for token in ("127.0.0.1", "localhost", "::1", "x-forwarded")
        ):
            raise ValueError("rate-limit key must not embed raw host material")

        now = max(0, int(now_ms))
        window_ms = int(route_limit.window_seconds) * 1000
        window_id = now // window_ms
        window_end_ms = (window_id + 1) * window_ms
        reset_after = max(0, (window_end_ms - now + 999) // 1000)
        reset_after = min(int(max_retry_after_seconds), max(1, reset_after) if reset_after else 0)
        # At exact window boundary remaining time can be 0 until next ms; clamp reset.
        if reset_after == 0:
            reset_after = int(route_limit.window_seconds)
        reset_after = min(int(max_retry_after_seconds), max(1, reset_after))

        merged_limits = tuple(sorted(set(self.limitations) | set(limitations)))

        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None or bucket.window_id != window_id:
                bucket = _WindowBucket(window_id=window_id, count=0)
                self._buckets[key] = bucket

            if bucket.count >= route_limit.max_requests:
                retry = min(int(max_retry_after_seconds), max(1, reset_after))
                return RateLimitDecision.limited_decision(
                    limit=route_limit.max_requests,
                    remaining=0,
                    retry_after_seconds=retry,
                    reset_after_seconds=retry,
                    safe_scope_reference=safe_scope_reference,
                    policy_id=policy_id,
                    limitations=merged_limits,
                )

            bucket.count += 1
            remaining = max(0, route_limit.max_requests - bucket.count)
            return RateLimitDecision.allowed_decision(
                limit=route_limit.max_requests,
                remaining=remaining,
                reset_after_seconds=reset_after,
                safe_scope_reference=safe_scope_reference,
                policy_id=policy_id,
                limitations=merged_limits,
            )

    def clear(self) -> None:
        with self._lock:
            self._buckets.clear()

    def key_snapshot(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._buckets.keys()))


def window_id_for(*, now_ms: int, window_seconds: int) -> int:
    window_ms = max(1, int(window_seconds)) * 1000
    return max(0, int(now_ms)) // window_ms


def make_evaluation_key(
    *,
    policy_token: str,
    scope_salt_version: str,
    group: str,
    safe_scope: str,
    now_ms: int,
    window_seconds: int,
    policy: object | None = None,
    route_limit: RouteRateLimit | None = None,
    scope: object | None = None,
) -> str:
    """Helper for tests — prefer scopes.build_rate_limit_key in production path."""

    from codestrata_platform.community_cloud_api.rate_limiting.models import (
        CommunityRateLimitPolicy,
    )
    from codestrata_platform.community_cloud_api.rate_limiting.scopes import RateLimitScope

    if (
        isinstance(policy, CommunityRateLimitPolicy)
        and route_limit is not None
        and isinstance(scope, RateLimitScope)
    ):
        return build_rate_limit_key(
            policy=policy,
            route_limit=route_limit,
            scope=scope,
            window_id=window_id_for(now_ms=now_ms, window_seconds=window_seconds),
        )
    _ = (policy_token, scope_salt_version, group, safe_scope)
    raise TypeError("make_evaluation_key requires policy, route_limit, and scope")

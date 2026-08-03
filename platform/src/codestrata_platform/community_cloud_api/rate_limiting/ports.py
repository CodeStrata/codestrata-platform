"""Persistence-neutral rate-limit store ports."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.community_cloud_api.rate_limiting.decisions import (
    RateLimitDecision,
)
from codestrata_platform.community_cloud_api.rate_limiting.models import RouteRateLimit


class RateLimitStore(Protocol):
    """Evaluate and consume capacity for a rate-limit key."""

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
    ) -> RateLimitDecision: ...


class UnavailableRateLimitStore:
    """Explicit unavailable store — never silently accepts unlimited traffic."""

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
        _ = (key, now_ms, max_retry_after_seconds)
        return RateLimitDecision.unavailable_decision(
            limit=route_limit.max_requests,
            safe_scope_reference=safe_scope_reference,
            policy_id=policy_id,
            limitations=tuple(
                sorted(
                    set(limitations)
                    | {"rate_limit_store_unavailable"}
                )
            ),
        )

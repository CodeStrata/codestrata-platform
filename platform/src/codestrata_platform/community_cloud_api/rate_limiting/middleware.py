"""Rate-limit evaluation helpers invoked from Community Cloud dispatch.

Not a global ASGI middleware that inspects bodies or forwarding headers.
Evaluation runs after route resolution and before request validation.
"""

from __future__ import annotations

from collections.abc import Callable

from starlette.responses import Response

from codestrata_platform.community_cloud_api.errors import (
    ERROR_RATE_LIMIT_EXCEEDED,
    ERROR_RATE_LIMIT_UNAVAILABLE,
)
from codestrata_platform.community_cloud_api.logging.context import LoggingContext
from codestrata_platform.community_cloud_api.logging.logger import CommunityCloudLogger
from codestrata_platform.community_cloud_api.rate_limiting.decisions import (
    DECISION_ALLOWED,
    DECISION_LIMITED,
    DECISION_UNAVAILABLE,
    RateLimitDecision,
)
from codestrata_platform.community_cloud_api.rate_limiting.diagnostics import (
    RateLimitDiagnostics,
)
from codestrata_platform.community_cloud_api.rate_limiting.limiter import (
    InMemoryRateLimitStore,
    window_id_for,
)
from codestrata_platform.community_cloud_api.rate_limiting.models import (
    CLIENT_SCOPE_AUTHENTICATED_PREFERRED,
    RATE_LIMIT_GROUP_AUTH_ATTEMPT,
    RATE_LIMIT_GROUP_HEALTH,
    UNAVAILABLE_REJECT_INGESTION_HEALTH_LOCAL,
    CommunityRateLimitPolicy,
    RouteRateLimit,
)
from codestrata_platform.community_cloud_api.rate_limiting.ports import (
    RateLimitStore,
    UnavailableRateLimitStore,
)
from codestrata_platform.community_cloud_api.rate_limiting.responses import (
    apply_allowed_rate_limit_headers,
    build_rate_limit_exceeded_response,
    build_rate_limit_unavailable_response,
)
from codestrata_platform.community_cloud_api.rate_limiting.scopes import (
    build_rate_limit_key,
    derive_authenticated_scope,
    derive_transport_scope,
)
from codestrata_platform.community_cloud_api.registry import RouteSpec


ClockMs = Callable[[], int]


class RateLimitRuntime:
    """Bundled policy/store/clock used by application dispatch."""

    def __init__(
        self,
        *,
        policy: CommunityRateLimitPolicy,
        store: RateLimitStore,
        clock_ms: ClockMs,
        health_fallback_store: InMemoryRateLimitStore | None = None,
    ) -> None:
        self.policy = policy
        self.store = store
        self.clock_ms = clock_ms
        self.health_fallback_store = health_fallback_store or InMemoryRateLimitStore()
        self.last_diagnostics: RateLimitDiagnostics | None = None

    def evaluate_route(
        self,
        *,
        route: RouteSpec,
        asgi_client_host: str | None,
        logger: CommunityCloudLogger,
        log_ctx: LoggingContext,
        api_version: str,
        request_id: str | None,
        authenticated_rate_limit_scope_id: str | None = None,
        auth_attempt: bool = False,
    ) -> tuple[RateLimitDecision | None, Response | None]:
        """Return (decision, None) when allowed, or (decision, response) when blocked.

        When policy is disabled, returns (None, None).
        """

        if not self.policy.enabled:
            self.last_diagnostics = RateLimitDiagnostics(
                route_id=route.name,
                decision_status="disabled",
                limit=0,
                remaining=0,
                retry_after_seconds=None,
                safe_scope_reference="",
                policy_id=self.policy.policy_id,
                store_status="disabled",
                limitations=("rate_limiting_disabled",),
            )
            return None, None

        if auth_attempt:
            route_limit = self.policy.auth_attempt_route_limit()
            scope = derive_transport_scope(
                policy=self.policy,
                route_limit=route_limit,
                asgi_client_host=asgi_client_host,
            )
            route_id_for_diag = "authentication.attempt"
        else:
            route_limit = self._route_limit_for(route)
            route_id_for_diag = route.name
            if (
                authenticated_rate_limit_scope_id
                and self.policy.client_scope_policy
                == CLIENT_SCOPE_AUTHENTICATED_PREFERRED
                and route_limit.group != RATE_LIMIT_GROUP_HEALTH
            ):
                scope = derive_authenticated_scope(
                    policy=self.policy,
                    route_limit=route_limit,
                    rate_limit_scope_id=authenticated_rate_limit_scope_id,
                )
            else:
                scope = derive_transport_scope(
                    policy=self.policy,
                    route_limit=route_limit,
                    asgi_client_host=asgi_client_host,
                )
        if scope.rejected:
            decision = RateLimitDecision.unavailable_decision(
                limit=route_limit.max_requests,
                safe_scope_reference="",
                policy_id=self.policy.policy_id,
                limitations=("missing_client_scope_rejected",),
            )
            self._record(route_id_for_diag, decision, store_status="missing_scope_rejected")
            logger.rate_limit_unavailable(
                log_ctx,
                status_code=503,
                decision=decision,
                safe_log_policy=self.policy.safe_log_policy,
            )
            return decision, build_rate_limit_unavailable_response(
                decision, api_version=api_version, request_id=request_id
            )
        if scope.unavailable:
            decision = RateLimitDecision.unavailable_decision(
                limit=route_limit.max_requests,
                safe_scope_reference="",
                policy_id=self.policy.policy_id,
                limitations=("missing_client_scope_unavailable",),
            )
            self._record(route_id_for_diag, decision, store_status="missing_scope_unavailable")
            logger.rate_limit_unavailable(
                log_ctx,
                status_code=503,
                decision=decision,
                safe_log_policy=self.policy.safe_log_policy,
            )
            return decision, build_rate_limit_unavailable_response(
                decision, api_version=api_version, request_id=request_id
            )

        try:
            now_ms = int(self.clock_ms())
        except Exception:  # noqa: BLE001
            decision = RateLimitDecision.unavailable_decision(
                limit=route_limit.max_requests,
                safe_scope_reference=scope.safe_scope_reference,
                policy_id=self.policy.policy_id,
                limitations=("rate_limit_clock_failure",),
            )
            self._record(route_id_for_diag, decision, store_status="clock_failure")
            logger.rate_limit_unavailable(
                log_ctx,
                status_code=503,
                decision=decision,
                safe_log_policy=self.policy.safe_log_policy,
            )
            return decision, build_rate_limit_unavailable_response(
                decision, api_version=api_version, request_id=request_id
            )

        key = build_rate_limit_key(
            policy=self.policy,
            route_limit=route_limit,
            scope=scope,
            window_id=window_id_for(
                now_ms=now_ms, window_seconds=route_limit.window_seconds
            ),
        )
        decision, store_status = self._evaluate_with_store(
            key=key,
            route_limit=route_limit,
            now_ms=now_ms,
            safe_scope_reference=scope.safe_scope_reference,
        )
        self._record(route_id_for_diag, decision, store_status=store_status)

        if decision.status == DECISION_ALLOWED:
            logger.rate_limit_allowed(
                log_ctx,
                status_code=None,
                decision=decision,
                safe_log_policy=self.policy.safe_log_policy,
            )
            return decision, None

        if decision.status == DECISION_LIMITED:
            logger.rate_limit_exceeded(
                log_ctx,
                status_code=429,
                decision=decision,
                safe_log_policy=self.policy.safe_log_policy,
            )
            return decision, build_rate_limit_exceeded_response(
                decision,
                api_version=api_version,
                request_id=request_id,
                policy=self.policy,
            )

        logger.rate_limit_unavailable(
            log_ctx,
            status_code=503,
            decision=decision,
            safe_log_policy=self.policy.safe_log_policy,
        )
        return decision, build_rate_limit_unavailable_response(
            decision, api_version=api_version, request_id=request_id
        )

    def attach_allowed_headers(
        self,
        response: Response,
        decision: RateLimitDecision | None,
    ) -> Response:
        if decision is None or decision.status != DECISION_ALLOWED:
            return response
        return apply_allowed_rate_limit_headers(
            response, decision, policy=self.policy
        )

    def _route_limit_for(self, route: RouteSpec) -> RouteRateLimit:
        try:
            return self.policy.limit_for_route(route.name)
        except ValueError:
            # Non-production / test-only routes use policy defaults.
            return RouteRateLimit(
                route_id=route.name,
                group=route.rate_limit_group,
                max_requests=self.policy.default_limit,
                window_seconds=self.policy.window_seconds,
            )

    def _evaluate_with_store(
        self,
        *,
        key: str,
        route_limit: RouteRateLimit,
        now_ms: int,
        safe_scope_reference: str,
    ) -> tuple[RateLimitDecision, str]:
        store = self.store
        store_status = "primary"
        try:
            decision = store.evaluate(
                key,
                route_limit=route_limit,
                now_ms=now_ms,
                max_retry_after_seconds=self.policy.max_retry_after_seconds,
                safe_scope_reference=safe_scope_reference,
                policy_id=self.policy.policy_id,
                limitations=self.policy.limitations,
            )
        except Exception:  # noqa: BLE001
            decision = RateLimitDecision.unavailable_decision(
                limit=route_limit.max_requests,
                safe_scope_reference=safe_scope_reference,
                policy_id=self.policy.policy_id,
                limitations=("rate_limit_store_exception",),
            )
            store_status = "exception"
            return decision, store_status

        if decision.status != DECISION_UNAVAILABLE:
            return decision, store_status

        if (
            route_limit.group == RATE_LIMIT_GROUP_HEALTH
            and self.policy.limiter_unavailable_behavior
            == UNAVAILABLE_REJECT_INGESTION_HEALTH_LOCAL
        ):
            fallback = self.health_fallback_store.evaluate(
                key,
                route_limit=route_limit,
                now_ms=now_ms,
                max_retry_after_seconds=self.policy.max_retry_after_seconds,
                safe_scope_reference=safe_scope_reference,
                policy_id=self.policy.policy_id,
                limitations=tuple(
                    sorted(
                        set(self.policy.limitations)
                        | {"health_process_local_fallback"}
                    )
                ),
            )
            return fallback, "health_fallback"

        return decision, "unavailable"

    def _record(
        self,
        route_id: str,
        decision: RateLimitDecision,
        *,
        store_status: str,
    ) -> None:
        self.last_diagnostics = RateLimitDiagnostics(
            route_id=route_id,
            decision_status=decision.status,
            limit=decision.limit,
            remaining=decision.remaining,
            retry_after_seconds=decision.retry_after_seconds,
            safe_scope_reference=decision.safe_scope_reference,
            policy_id=decision.policy_id,
            store_status=store_status,
            limitations=decision.limitations,
        )


def default_rate_limit_runtime(
    *,
    policy: CommunityRateLimitPolicy | None = None,
    store: RateLimitStore | None = None,
    clock_ms: ClockMs | None = None,
) -> RateLimitRuntime:
    from codestrata_platform.community_cloud_api.rate_limiting.limiter import (
        monotonic_clock_ms,
    )
    from codestrata_platform.community_cloud_api.rate_limiting.policy import (
        default_rate_limit_policy,
    )

    active_policy = policy or default_rate_limit_policy()
    active_store: RateLimitStore
    if store is None:
        active_store = InMemoryRateLimitStore()
    else:
        active_store = store
    return RateLimitRuntime(
        policy=active_policy,
        store=active_store,
        clock_ms=clock_ms or monotonic_clock_ms,
    )


# Re-export for type checkers / tests
__all__ = [
    "RateLimitRuntime",
    "default_rate_limit_runtime",
    "ERROR_RATE_LIMIT_EXCEEDED",
    "ERROR_RATE_LIMIT_UNAVAILABLE",
    "UnavailableRateLimitStore",
]

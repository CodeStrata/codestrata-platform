"""Rate-limit policy and group models for Community Cloud API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


COMMUNITY_RATE_LIMIT_POLICY_ID = "community-rate-limit-policy"
COMMUNITY_RATE_LIMIT_POLICY_VERSION = "1.1"
COMMUNITY_RATE_LIMIT_POLICY_URN = (
    f"{COMMUNITY_RATE_LIMIT_POLICY_ID}:{COMMUNITY_RATE_LIMIT_POLICY_VERSION}"
)

RATE_LIMIT_GROUP_HEALTH = "health"
RATE_LIMIT_GROUP_INGESTION = "ingestion"
RATE_LIMIT_GROUP_AUTH_ATTEMPT = "auth_attempt"
VALID_RATE_LIMIT_GROUPS = frozenset(
    {
        RATE_LIMIT_GROUP_HEALTH,
        RATE_LIMIT_GROUP_INGESTION,
        RATE_LIMIT_GROUP_AUTH_ATTEMPT,
    }
)

ALGORITHM_FIXED_WINDOW = "fixed_window"

CLIENT_SCOPE_DIRECT_ASGI_HOST = "direct_asgi_host"
CLIENT_SCOPE_AUTHENTICATED_PREFERRED = "authenticated_preferred"
MISSING_SCOPE_GLOBAL_ANONYMOUS = "global_anonymous_scope"
MISSING_SCOPE_REJECT = "reject"
MISSING_SCOPE_LIMITER_UNAVAILABLE = "limiter_unavailable"

UNAVAILABLE_REJECT = "reject"
UNAVAILABLE_REJECT_INGESTION_HEALTH_LOCAL = "reject_ingestion_health_local"

SCOPE_SALT_VERSION = "scope-v1"

GLOBAL_ANONYMOUS_HOST_TOKEN = "global_anonymous"

PRODUCTION_ROUTE_IDS: tuple[str, ...] = (
    "health.get",
    "telemetry.ingest",
    "assessment_metadata.ingest",
    "cli_events.ingest",
    "extension_events.ingest",
    "ai_usage.ingest",
)

DEFAULT_AUTH_ATTEMPT_MAX_REQUESTS = 60
DEFAULT_HEALTH_MAX_REQUESTS = 120
DEFAULT_INGESTION_MAX_REQUESTS = 30
DEFAULT_WINDOW_SECONDS = 60
DEFAULT_MAX_RETRY_AFTER_SECONDS = 60


@dataclass(frozen=True, slots=True)
class RouteRateLimit:
    """Per-route rate-limit descriptor attached via policy mapping."""

    route_id: str
    group: str
    max_requests: int
    window_seconds: int

    def __post_init__(self) -> None:
        route_id = (self.route_id or "").strip()
        group = (self.group or "").strip()
        if not route_id:
            raise ValueError("route_id is required")
        if group not in VALID_RATE_LIMIT_GROUPS:
            raise ValueError(f"invalid rate-limit group: {group}")
        if int(self.max_requests) < 1:
            raise ValueError("max_requests must be >= 1")
        if int(self.window_seconds) < 1:
            raise ValueError("window_seconds must be >= 1")
        object.__setattr__(self, "route_id", route_id)
        object.__setattr__(self, "group", group)
        object.__setattr__(self, "max_requests", int(self.max_requests))
        object.__setattr__(self, "window_seconds", int(self.window_seconds))

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "group": self.group,
            "max_requests": self.max_requests,
            "route_id": self.route_id,
            "window_seconds": self.window_seconds,
        }


@dataclass(frozen=True, slots=True)
class ResponseHeaderPolicy:
    """Which RateLimit-* headers to emit."""

    include_on_allowed: bool = True
    include_on_limited: bool = True
    include_retry_after_on_limited: bool = True

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "include_on_allowed": self.include_on_allowed,
            "include_on_limited": self.include_on_limited,
            "include_retry_after_on_limited": self.include_retry_after_on_limited,
        }


@dataclass(frozen=True, slots=True)
class SafeLogPolicy:
    """Bounded safe fields for rate-limit structured log events."""

    include_safe_scope_reference: bool = True
    include_limit_fields: bool = True

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "include_limit_fields": self.include_limit_fields,
            "include_safe_scope_reference": self.include_safe_scope_reference,
        }


@dataclass(frozen=True, slots=True)
class CommunityRateLimitPolicy:
    """Deterministic Community Cloud rate-limit policy (v1.1).

    Slice 7.13: authenticated client scope is primary for protected ingestion;
    transport scope remains for health and pre-auth attempt throttling.
    """

    policy_id: str = COMMUNITY_RATE_LIMIT_POLICY_ID
    policy_version: str = COMMUNITY_RATE_LIMIT_POLICY_URN
    enabled: bool = True
    algorithm: str = ALGORITHM_FIXED_WINDOW
    route_limits: tuple[RouteRateLimit, ...] = ()
    default_limit: int = DEFAULT_INGESTION_MAX_REQUESTS
    health_limit: int = DEFAULT_HEALTH_MAX_REQUESTS
    ingestion_limit: int = DEFAULT_INGESTION_MAX_REQUESTS
    auth_attempt_limit: int = DEFAULT_AUTH_ATTEMPT_MAX_REQUESTS
    window_seconds: int = DEFAULT_WINDOW_SECONDS
    burst_capacity: int = DEFAULT_INGESTION_MAX_REQUESTS
    client_scope_policy: str = CLIENT_SCOPE_AUTHENTICATED_PREFERRED
    missing_scope_behavior: str = MISSING_SCOPE_GLOBAL_ANONYMOUS
    limiter_unavailable_behavior: str = UNAVAILABLE_REJECT_INGESTION_HEALTH_LOCAL
    scope_salt_version: str = SCOPE_SALT_VERSION
    max_retry_after_seconds: int = DEFAULT_MAX_RETRY_AFTER_SECONDS
    response_header_policy: ResponseHeaderPolicy = ResponseHeaderPolicy()
    safe_log_policy: SafeLogPolicy = SafeLogPolicy()
    limitations: tuple[str, ...] = (
        "process_local_in_memory_store_default",
        "not_distributed_enforcement",
        "no_forwarded_header_trust",
        "authenticated_scope_for_ingestion",
        "transport_scope_for_health_and_auth_attempts",
        "trusted_proxy_support_deferred",
        "development_defaults_not_final_production_limits",
    )

    def __post_init__(self) -> None:
        if self.policy_id != COMMUNITY_RATE_LIMIT_POLICY_ID:
            raise ValueError("unsupported rate-limit policy id")
        if self.policy_version != COMMUNITY_RATE_LIMIT_POLICY_URN:
            raise ValueError("unsupported rate-limit policy version")
        if self.algorithm != ALGORITHM_FIXED_WINDOW:
            raise ValueError(f"unsupported rate-limit algorithm: {self.algorithm}")
        if self.client_scope_policy not in {
            CLIENT_SCOPE_DIRECT_ASGI_HOST,
            CLIENT_SCOPE_AUTHENTICATED_PREFERRED,
        }:
            raise ValueError("unsupported client_scope_policy")
        if self.missing_scope_behavior not in {
            MISSING_SCOPE_GLOBAL_ANONYMOUS,
            MISSING_SCOPE_REJECT,
            MISSING_SCOPE_LIMITER_UNAVAILABLE,
        }:
            raise ValueError("invalid missing_scope_behavior")
        if self.limiter_unavailable_behavior not in {
            UNAVAILABLE_REJECT,
            UNAVAILABLE_REJECT_INGESTION_HEALTH_LOCAL,
        }:
            raise ValueError("invalid limiter_unavailable_behavior")
        if not (self.scope_salt_version or "").strip():
            raise ValueError("scope_salt_version is required")
        for name in (
            "default_limit",
            "health_limit",
            "ingestion_limit",
            "auth_attempt_limit",
            "window_seconds",
            "burst_capacity",
            "max_retry_after_seconds",
        ):
            value = int(getattr(self, name))
            if value < 1:
                raise ValueError(f"{name} must be >= 1")
            object.__setattr__(self, name, value)
        if self.burst_capacity < self.ingestion_limit:
            raise ValueError("burst_capacity must be >= ingestion_limit")

        limits = tuple(
            sorted(self.route_limits, key=lambda item: (item.group, item.route_id))
        )
        seen: set[str] = set()
        for item in limits:
            if item.route_id in seen:
                raise ValueError(f"duplicate route rate-limit: {item.route_id}")
            seen.add(item.route_id)
        object.__setattr__(self, "route_limits", limits)
        object.__setattr__(
            self,
            "limitations",
            tuple(sorted(str(item) for item in self.limitations)),
        )
        _assert_production_coverage(limits)

    @classmethod
    def default(cls) -> CommunityRateLimitPolicy:
        window = DEFAULT_WINDOW_SECONDS
        return cls(
            route_limits=_default_route_limits(
                health_limit=DEFAULT_HEALTH_MAX_REQUESTS,
                ingestion_limit=DEFAULT_INGESTION_MAX_REQUESTS,
                window_seconds=window,
            ),
            default_limit=DEFAULT_INGESTION_MAX_REQUESTS,
            health_limit=DEFAULT_HEALTH_MAX_REQUESTS,
            ingestion_limit=DEFAULT_INGESTION_MAX_REQUESTS,
            auth_attempt_limit=DEFAULT_AUTH_ATTEMPT_MAX_REQUESTS,
            window_seconds=window,
            burst_capacity=DEFAULT_INGESTION_MAX_REQUESTS,
        )

    def auth_attempt_route_limit(self) -> RouteRateLimit:
        return RouteRateLimit(
            route_id="authentication.attempt",
            group=RATE_LIMIT_GROUP_AUTH_ATTEMPT,
            max_requests=self.auth_attempt_limit,
            window_seconds=self.window_seconds,
        )

    def policy_token(self) -> str:
        """Deterministic policy identity token used in scope/key material."""

        return self.policy_version

    def limit_for_route(self, route_id: str) -> RouteRateLimit:
        for item in self.route_limits:
            if item.route_id == route_id:
                return item
        raise ValueError(f"missing rate-limit policy for route: {route_id}")

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "auth_attempt_limit": self.auth_attempt_limit,
            "burst_capacity": self.burst_capacity,
            "client_scope_policy": self.client_scope_policy,
            "default_limit": self.default_limit,
            "enabled": self.enabled,
            "health_limit": self.health_limit,
            "ingestion_limit": self.ingestion_limit,
            "limitations": list(self.limitations),
            "limiter_unavailable_behavior": self.limiter_unavailable_behavior,
            "max_retry_after_seconds": self.max_retry_after_seconds,
            "missing_scope_behavior": self.missing_scope_behavior,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "response_header_policy": self.response_header_policy.to_stable_dict(),
            "route_limits": [item.to_stable_dict() for item in self.route_limits],
            "safe_log_policy": self.safe_log_policy.to_stable_dict(),
            "scope_salt_version": self.scope_salt_version,
            "window_seconds": self.window_seconds,
        }


def _default_route_limits(
    *,
    health_limit: int,
    ingestion_limit: int,
    window_seconds: int,
) -> tuple[RouteRateLimit, ...]:
    health = RouteRateLimit(
        route_id="health.get",
        group=RATE_LIMIT_GROUP_HEALTH,
        max_requests=health_limit,
        window_seconds=window_seconds,
    )
    ingestion_routes = (
        "telemetry.ingest",
        "assessment_metadata.ingest",
        "cli_events.ingest",
        "extension_events.ingest",
        "ai_usage.ingest",
    )
    ingestion = tuple(
        RouteRateLimit(
            route_id=route_id,
            group=RATE_LIMIT_GROUP_INGESTION,
            max_requests=ingestion_limit,
            window_seconds=window_seconds,
        )
        for route_id in ingestion_routes
    )
    return (health, *ingestion)


def _assert_production_coverage(limits: tuple[RouteRateLimit, ...]) -> None:
    covered = {item.route_id for item in limits}
    expected = set(PRODUCTION_ROUTE_IDS)
    missing = sorted(expected - covered)
    unknown = sorted(covered - expected)
    if missing:
        raise ValueError(f"missing rate-limit policies for routes: {missing}")
    if unknown:
        raise ValueError(f"unknown route rate-limit policies: {unknown}")
    by_group: dict[str, set[str]] = {}
    for item in limits:
        by_group.setdefault(item.group, set()).add(item.route_id)
    if "health.get" not in by_group.get(RATE_LIMIT_GROUP_HEALTH, set()):
        raise ValueError("health.get must use health rate-limit group")
    ingestion_expected = set(PRODUCTION_ROUTE_IDS) - {"health.get"}
    if by_group.get(RATE_LIMIT_GROUP_INGESTION, set()) != ingestion_expected:
        raise ValueError("ingestion routes must use ingestion rate-limit group")


def assert_supported_rate_limit_policy(
    policy: CommunityRateLimitPolicy,
) -> CommunityRateLimitPolicy:
    if policy.policy_version != COMMUNITY_RATE_LIMIT_POLICY_URN:
        raise ValueError(f"unsupported rate-limit policy: {policy.policy_version}")
    return policy


def assert_policy_covers_registry_routes(
    policy: CommunityRateLimitPolicy,
    route_names: Mapping[str, str] | frozenset[str] | set[str] | tuple[str, ...],
) -> None:
    """Require explicit policy for every production route present in the registry.

    Test-only / custom routes may exist without a dedicated policy entry; they
    receive ``default_limit`` at evaluation time.
    """

    if isinstance(route_names, Mapping):
        names = set(route_names.keys())
    else:
        names = set(route_names)
    covered = {item.route_id for item in policy.route_limits}
    production_present = names & set(PRODUCTION_ROUTE_IDS)
    missing = sorted(production_present - covered)
    if missing:
        raise ValueError(f"rate-limit policy missing routes: {missing}")

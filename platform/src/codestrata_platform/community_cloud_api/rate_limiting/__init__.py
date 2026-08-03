"""Community Cloud API rate limiting (Slice 7.12).

Process-local in-memory enforcement by default. Persistence-neutral ports only.
Does not authenticate clients or trust forwarding headers.
"""

from __future__ import annotations

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
    monotonic_clock_ms,
)
from codestrata_platform.community_cloud_api.rate_limiting.middleware import (
    RateLimitRuntime,
    default_rate_limit_runtime,
)
from codestrata_platform.community_cloud_api.rate_limiting.models import (
    COMMUNITY_RATE_LIMIT_POLICY_ID,
    COMMUNITY_RATE_LIMIT_POLICY_URN,
    COMMUNITY_RATE_LIMIT_POLICY_VERSION,
    PRODUCTION_ROUTE_IDS,
    RATE_LIMIT_GROUP_HEALTH,
    RATE_LIMIT_GROUP_INGESTION,
    CommunityRateLimitPolicy,
    RouteRateLimit,
)
from codestrata_platform.community_cloud_api.rate_limiting.policy import (
    ACTIVE_RATE_LIMIT_POLICY,
    default_rate_limit_policy,
    validate_rate_limit_policy,
)
from codestrata_platform.community_cloud_api.rate_limiting.ports import (
    RateLimitStore,
    UnavailableRateLimitStore,
)
from codestrata_platform.community_cloud_api.rate_limiting.scopes import (
    RateLimitScope,
    derive_transport_scope,
)

__all__ = [
    "ACTIVE_RATE_LIMIT_POLICY",
    "COMMUNITY_RATE_LIMIT_POLICY_ID",
    "COMMUNITY_RATE_LIMIT_POLICY_URN",
    "COMMUNITY_RATE_LIMIT_POLICY_VERSION",
    "DECISION_ALLOWED",
    "DECISION_LIMITED",
    "DECISION_UNAVAILABLE",
    "PRODUCTION_ROUTE_IDS",
    "RATE_LIMIT_GROUP_HEALTH",
    "RATE_LIMIT_GROUP_INGESTION",
    "CommunityRateLimitPolicy",
    "InMemoryRateLimitStore",
    "RateLimitDecision",
    "RateLimitDiagnostics",
    "RateLimitRuntime",
    "RateLimitScope",
    "RateLimitStore",
    "RouteRateLimit",
    "UnavailableRateLimitStore",
    "default_rate_limit_policy",
    "default_rate_limit_runtime",
    "derive_transport_scope",
    "monotonic_clock_ms",
    "validate_rate_limit_policy",
]

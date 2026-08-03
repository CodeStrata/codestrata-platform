"""Privacy-safe transport scope derivation for rate limiting."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from codestrata_platform.community_cloud_api.rate_limiting.models import (
    GLOBAL_ANONYMOUS_HOST_TOKEN,
    MISSING_SCOPE_GLOBAL_ANONYMOUS,
    MISSING_SCOPE_LIMITER_UNAVAILABLE,
    MISSING_SCOPE_REJECT,
    CommunityRateLimitPolicy,
    RouteRateLimit,
)


@dataclass(frozen=True, slots=True)
class RateLimitScope:
    """Transient rate-limit scope — never an authentication identity."""

    safe_scope: str
    safe_scope_reference: str
    used_global_anonymous: bool
    rejected: bool = False
    unavailable: bool = False

    def to_stable_dict(self) -> dict[str, object]:
        return {
            "rejected": self.rejected,
            "safe_scope": self.safe_scope,
            "safe_scope_reference": self.safe_scope_reference,
            "unavailable": self.unavailable,
            "used_global_anonymous": self.used_global_anonymous,
        }


def derive_transport_scope(
    *,
    policy: CommunityRateLimitPolicy,
    route_limit: RouteRateLimit,
    asgi_client_host: str | None,
) -> RateLimitScope:
    """Derive a policy-bound one-way scope from direct ASGI client host only.

    Never reads forwarding headers. Never persists or returns the raw host.
    """

    host = _normalize_host(asgi_client_host)
    used_global = False
    if host is None:
        if policy.missing_scope_behavior == MISSING_SCOPE_REJECT:
            return RateLimitScope(
                safe_scope="",
                safe_scope_reference="",
                used_global_anonymous=False,
                rejected=True,
            )
        if policy.missing_scope_behavior == MISSING_SCOPE_LIMITER_UNAVAILABLE:
            return RateLimitScope(
                safe_scope="",
                safe_scope_reference="",
                used_global_anonymous=False,
                unavailable=True,
            )
        if policy.missing_scope_behavior != MISSING_SCOPE_GLOBAL_ANONYMOUS:
            raise ValueError("invalid missing_scope_behavior")
        host = GLOBAL_ANONYMOUS_HOST_TOKEN
        used_global = True

    digest = _scope_digest(
        policy_token=policy.policy_token(),
        scope_salt_version=policy.scope_salt_version,
        group=route_limit.group,
        host_material=host,
    )
    return RateLimitScope(
        safe_scope=f"rate-scope:{digest[:24]}",
        safe_scope_reference=f"rls-{digest[:12]}",
        used_global_anonymous=used_global,
    )


def derive_authenticated_scope(
    *,
    policy: CommunityRateLimitPolicy,
    route_limit: RouteRateLimit,
    rate_limit_scope_id: str,
) -> RateLimitScope:
    """Derive authenticated rate-limit scope from opaque rate_limit_scope_id.

    Never uses raw credentials, event IDs, request IDs, or IP addresses.
    """

    material_id = (rate_limit_scope_id or "").strip()
    if not material_id:
        return RateLimitScope(
            safe_scope="",
            safe_scope_reference="",
            used_global_anonymous=False,
            unavailable=True,
        )
    digest = hashlib.sha256(
        "|".join(
            (
                policy.policy_token(),
                policy.scope_salt_version,
                "authenticated",
                route_limit.group,
                material_id,
            )
        ).encode("utf-8")
    ).hexdigest()
    return RateLimitScope(
        safe_scope=f"auth-scope:{digest[:24]}",
        safe_scope_reference=f"rls-{digest[:12]}",
        used_global_anonymous=False,
    )


def build_rate_limit_key(
    *,
    policy: CommunityRateLimitPolicy,
    route_limit: RouteRateLimit,
    scope: RateLimitScope,
    window_id: int,
) -> str:
    """Internal store key — hashed material only; never expose in responses."""

    material = "|".join(
        (
            policy.policy_token(),
            policy.scope_salt_version,
            route_limit.group,
            scope.safe_scope,
            str(int(window_id)),
        )
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return f"rate:{digest[:24]}"


def _normalize_host(host: str | None) -> str | None:
    if host is None:
        return None
    text = host.strip()
    if not text or any(ch.isspace() for ch in text):
        return None
    return text


def _scope_digest(
    *,
    policy_token: str,
    scope_salt_version: str,
    group: str,
    host_material: str,
) -> str:
    material = "|".join(
        (policy_token, scope_salt_version, group, host_material)
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()

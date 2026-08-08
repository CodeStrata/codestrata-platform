"""CORS helpers for Insights credentialed requests — no wildcard with cookies."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.insights_auth.policy import InsightsAuthPolicy


def cors_headers_for_origin(
    *,
    request_origin: str | None,
    policy: InsightsAuthPolicy,
    extra_allowed_origins: frozenset[str] | None = None,
) -> dict[str, str] | None:
    """Return ACAO/credentials headers only for an explicit allowed origin.

    Production topology is same-origin proxy, so CORS is unused there.
    Local Vite origins may be listed in extra_allowed_origins (test/dev only).
    """

    if policy.cors_wildcard_with_credentials:
        return None  # Forbidden posture — caller must not enable this.

    origin = (request_origin or "").strip().rstrip("/")
    if not origin:
        return None

    allowed = {policy.future_frontend_origin.rstrip("/")}
    if extra_allowed_origins:
        allowed |= {o.rstrip("/") for o in extra_allowed_origins}
    if origin not in allowed:
        return None

    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,X-Request-Id",
        "Vary": "Origin",
    }

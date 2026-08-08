"""CSRF posture for cookie-authenticated Insights auth endpoints."""

from __future__ import annotations

from urllib.parse import urlparse

from codestrata_platform.community_cloud_api.insights_auth.policy import InsightsAuthPolicy


def origin_allowed(
    *,
    origin: str | None,
    referer: str | None,
    policy: InsightsAuthPolicy,
    extra_allowed_origins: frozenset[str] | None = None,
) -> bool:
    """Validate Origin (preferred) or Referer for state-changing requests.

    SameSite=Strict is the primary CSRF control for production same-origin
    topology. Origin checks apply when a header is present. Missing Origin and
    Referer is allowed for same-origin navigations that omit them (e.g. some
    non-browser clients in tests); production browsers send Origin on POST.
    """

    allowed = {policy.future_frontend_origin.rstrip("/")}
    if extra_allowed_origins:
        allowed |= {o.rstrip("/") for o in extra_allowed_origins}

    candidate = (origin or "").strip()
    if candidate:
        return candidate.rstrip("/") in allowed

    ref = (referer or "").strip()
    if ref:
        parsed = urlparse(ref)
        if not parsed.scheme or not parsed.netloc:
            return False
        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/") in allowed

    # No Origin/Referer — accept for local/test clients; SameSite still binds browsers.
    return True

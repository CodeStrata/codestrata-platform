"""HttpOnly Secure SameSite cookie helpers for Insights sessions."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.insights_auth.policy import InsightsAuthPolicy


def parse_cookie_header(cookie_header: str | None, name: str) -> str | None:
    if not cookie_header:
        return None
    for part in cookie_header.split(";"):
        item = part.strip()
        if not item or "=" not in item:
            continue
        key, value = item.split("=", 1)
        if key.strip() == name:
            return value.strip() or None
    return None


def build_set_cookie(
    *,
    policy: InsightsAuthPolicy,
    token: str,
    max_age: int | None = None,
    clear: bool = False,
) -> str:
    """Build a single Set-Cookie header value (no Domain — host-only)."""

    age = 0 if clear else int(max_age if max_age is not None else policy.session_ttl_seconds)
    value = "" if clear else token
    parts = [
        f"{policy.cookie_name}={value}",
        f"Path={policy.cookie_path}",
        f"Max-Age={age}",
        f"SameSite={policy.same_site_policy}",
    ]
    if policy.http_only_cookie:
        parts.append("HttpOnly")
    if policy.secure_cookie:
        parts.append("Secure")
    return "; ".join(parts)


def cookie_flags_ok(set_cookie: str, *, require_secure: bool = True) -> bool:
    lower = set_cookie.lower()
    if "httponly" not in lower:
        return False
    if "samesite=" not in lower:
        return False
    if require_secure and "secure" not in lower:
        return False
    return True

"""Bounded Insights auth error codes — never expose AWS/secret details."""

from __future__ import annotations

ERROR_AUTHENTICATION_REQUIRED = "authentication_required"
ERROR_INVALID_CREDENTIALS = "invalid_credentials"
ERROR_SESSION_EXPIRED = "session_expired"
ERROR_INVALID_SESSION = "invalid_session"
ERROR_AUTHORIZATION_DENIED = "authorization_denied"
ERROR_AUTH_SERVICE_UNAVAILABLE = "auth_service_unavailable"
ERROR_INVALID_ORIGIN = "invalid_origin"
ERROR_RATE_LIMITED = "rate_limited"
ERROR_INTERNAL_AUTH = "internal_auth_error"

INSIGHTS_AUTH_ERROR_CODES = frozenset(
    {
        ERROR_AUTHENTICATION_REQUIRED,
        ERROR_INVALID_CREDENTIALS,
        ERROR_SESSION_EXPIRED,
        ERROR_INVALID_SESSION,
        ERROR_AUTHORIZATION_DENIED,
        ERROR_AUTH_SERVICE_UNAVAILABLE,
        ERROR_INVALID_ORIGIN,
        ERROR_RATE_LIMITED,
        ERROR_INTERNAL_AUTH,
    }
)

# Generic browser-visible messages (no secret/AWS detail).
SAFE_MESSAGES: dict[str, str] = {
    ERROR_AUTHENTICATION_REQUIRED: "Authentication required",
    ERROR_INVALID_CREDENTIALS: "Invalid password",
    ERROR_SESSION_EXPIRED: "Session expired",
    ERROR_INVALID_SESSION: "Invalid session",
    ERROR_AUTHORIZATION_DENIED: "Access denied",
    ERROR_AUTH_SERVICE_UNAVAILABLE: "Authentication unavailable",
    ERROR_INVALID_ORIGIN: "Invalid request origin",
    ERROR_RATE_LIMITED: "Too many requests",
    ERROR_INTERNAL_AUTH: "Authentication error",
}

"""Bounded operational diagnostics helpers (not an intelligence source of truth)."""

from __future__ import annotations

from codestrata_platform.security import sanitize_exception_message

# Stable operational error categories for structured logs and failure summaries.
VALIDATION = "validation"
AUTHORIZATION = "authorization"
NOT_FOUND = "not_found"
CONFLICT = "conflict"
CONFIGURATION = "configuration"
PROVIDER_AUTHENTICATION = "provider_authentication"
PROVIDER_RATE_LIMIT = "provider_rate_limit"
PROVIDER_TIMEOUT = "provider_timeout"
PROVIDER_UNAVAILABLE = "provider_unavailable"
PROVIDER_MALFORMED_RESPONSE = "provider_malformed_response"
DATABASE = "database"
PERSISTENCE_CONFLICT = "persistence_conflict"
TEMPORARY_RESOURCE = "temporary_resource"
CANCELLED = "cancelled"
INTERNAL = "internal"

_DEFAULT_FAILURE_LIMIT = 1000


def safe_failure_summary(
    error: BaseException | str,
    *,
    limit: int = _DEFAULT_FAILURE_LIMIT,
    database_url: str | None = None,
) -> str:
    """Return a truncated, secret-safe failure summary for persistence or APIs."""

    raw = str(error)
    sanitized = sanitize_exception_message(raw, database_url=database_url)
    bounded = max(1, int(limit))
    return sanitized[:bounded]


def classify_exception(error: BaseException) -> str:
    """Map an exception to a bounded operational category for logs."""

    reason = getattr(error, "reason_code", None)
    if isinstance(reason, str) and reason:
        lowered = reason.lower()
        if "disabled" in lowered or "config" in lowered:
            return CONFIGURATION
        if "not_found" in lowered or lowered.endswith("_missing"):
            return NOT_FOUND
        if "conflict" in lowered or "duplicate" in lowered:
            return CONFLICT
        if "unauthorized" in lowered or "forbidden" in lowered:
            return AUTHORIZATION
        if "validation" in lowered or "invalid" in lowered:
            return VALIDATION
        if "throttl" in lowered or "rate_limit" in lowered:
            return PROVIDER_RATE_LIMIT
        if "timeout" in lowered:
            return PROVIDER_TIMEOUT
        if "auth" in lowered:
            return PROVIDER_AUTHENTICATION

    name = type(error).__name__.lower()
    module = type(error).__module__.lower()
    text = f"{name} {module} {error!s}".lower()
    if "timeout" in text:
        return PROVIDER_TIMEOUT
    if "throttl" in text or "rate limit" in text or "ratelimit" in text:
        return PROVIDER_RATE_LIMIT
    if "auth" in text and ("provider" in text or "aws" in text or "openai" in text):
        return PROVIDER_AUTHENTICATION
    if "operationalerror" in name or "database" in text or "connection refused" in text:
        return DATABASE
    if "integrity" in name or "unique" in text:
        return PERSISTENCE_CONFLICT
    if "validation" in name or "valueerror" in name:
        return VALIDATION
    if "notfound" in name:
        return NOT_FOUND
    if "conflict" in name:
        return CONFLICT
    return INTERNAL


__all__ = [
    "AUTHORIZATION",
    "CANCELLED",
    "CONFIGURATION",
    "CONFLICT",
    "DATABASE",
    "INTERNAL",
    "NOT_FOUND",
    "PERSISTENCE_CONFLICT",
    "PROVIDER_AUTHENTICATION",
    "PROVIDER_MALFORMED_RESPONSE",
    "PROVIDER_RATE_LIMIT",
    "PROVIDER_TIMEOUT",
    "PROVIDER_UNAVAILABLE",
    "TEMPORARY_RESOURCE",
    "VALIDATION",
    "classify_exception",
    "safe_failure_summary",
]

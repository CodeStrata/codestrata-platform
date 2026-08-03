"""Redaction and truncation helpers for Community Cloud logs."""

from __future__ import annotations

import re
from collections.abc import Mapping

_SECRET_HEADER_NAMES = frozenset(
    {
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "proxy-authorization",
        "x-amz-security-token",
    }
)

_TOKENISH_RE = re.compile(
    r"(?i)(bearer\s+[a-z0-9._\-+/=]{8,}|eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+|"
    r"AKIA[0-9A-Z]{16})"
)
_PATHISH_RE = re.compile(r"(?i)(/Users/|/home/|[A-Za-z]:\\|file://)")


def truncate(value: str, *, max_length: int) -> str:
    text = value if isinstance(value, str) else str(value)
    if len(text) <= max_length:
        return text
    if max_length <= 3:
        return text[:max_length]
    return text[: max_length - 3] + "..."


def sanitize_request_id(value: str | None, *, max_length: int) -> str | None:
    if value is None:
        return None
    text = "".join(ch for ch in value.strip() if ch.isprintable() and ord(ch) >= 32)
    if not text:
        return None
    # Reject path/token shaped ids.
    if _PATHISH_RE.search(text) or _TOKENISH_RE.search(text):
        return None
    return truncate(text, max_length=max_length)


def sanitize_route(path: str, *, max_length: int) -> str:
    text = (path or "/").strip() or "/"
    # Keep URL path only — never filesystem paths.
    if _PATHISH_RE.search(text) and not text.startswith("/api/"):
        return "/redacted"
    return truncate(text, max_length=max_length)


def sanitize_method(method: str) -> str:
    return (method or "").strip().upper()[:16] or "UNKNOWN"


def sanitize_error_code(code: str | None, *, max_length: int) -> str | None:
    if code is None:
        return None
    text = "".join(ch for ch in code.strip() if ch.isalnum() or ch in "._-")
    if not text:
        return None
    return truncate(text, max_length=max_length)


def sanitize_client_host(host: str | None, *, max_length: int) -> str | None:
    if host is None:
        return None
    text = host.strip()
    if not text or any(ch.isspace() for ch in text):
        return None
    # Never trust forwarding headers — caller must pass ASGI client host only.
    if _PATHISH_RE.search(text) or _TOKENISH_RE.search(text):
        return None
    return truncate(text, max_length=max_length)


def is_secret_header_name(name: str) -> bool:
    return name.strip().lower() in _SECRET_HEADER_NAMES


def redact_header_value(name: str, value: str) -> str:
    if is_secret_header_name(name):
        return "[redacted]"
    if _TOKENISH_RE.search(value) or _PATHISH_RE.search(value):
        return "[redacted]"
    return value


def ensure_no_payload_fields(fields: dict[str, object]) -> dict[str, object]:
    forbidden = {
        "body",
        "payload",
        "authorization",
        "cookie",
        "password",
        "token",
        "secret",
        "api_key",
        "jwt",
        # Event-identity privacy: never log raw ids/fingerprints via free-form fields.
        "event_id",
        "payload_fingerprint",
        "installation_id",
        "event_key",
        "credential",
        "credential_fingerprint",
        "bearer",
        "api_key",
        "secret",
        "token",
    }
    return {
        key: value
        for key, value in fields.items()
        if key.lower() not in forbidden
    }


def assert_safe_event_log_fields(fields: Mapping[str, object]) -> dict[str, object]:
    """Allow only explicit safe event-identity / telemetry log fields."""

    allowed = {
        "safe_event_reference",
        "retry_status",
        "source_event_type",
        "identity_policy_version",
        "telemetry_schema_version",
        "telemetry_policy_version",
        "metadata_schema_version",
        "metadata_policy_version",
        "client_type",
        "assessment_status",
        "cli_schema_version",
        "cli_policy_version",
        "canonical_operation",
        "lifecycle",
        "result",
        "extension_schema_version",
        "extension_policy_version",
        "ai_schema_version",
        "ai_policy_version",
        "canonical_capability",
        "outcome",
        "rate_limit_policy_id",
        "rate_limit_limit",
        "rate_limit_remaining",
        "retry_after_seconds",
        "safe_scope_reference",
        "authentication_policy_id",
        "authentication_reason",
        "verifier_status",
        "safe_client_reference",
        "client_type",
    }
    cleaned = ensure_no_payload_fields(dict(fields))
    return {key: cleaned[key] for key in sorted(cleaned) if key in allowed}

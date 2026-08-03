"""Event-identity validation helpers and conflict error builders."""

from __future__ import annotations

import re

from codestrata_platform.community_cloud_api.errors import (
    ERROR_EVENT_IDENTITY_CONFLICT,
    ApiErrorResponse,
)
from codestrata_platform.community_cloud_api.event_identity.models import (
    CommunityEventIdentityPolicy,
)
from codestrata_platform.community_cloud_api.validation.sanitization import (
    contains_secret_like_value,
    reject_control_characters,
)

_EVENT_ID_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
_URLISH_RE = re.compile(r"(?i)^(https?://|file://)")


def validate_event_id_text(
    value: str,
    *,
    policy: CommunityEventIdentityPolicy | None = None,
) -> str:
    """Validate a raw event_id string against the identity policy."""

    active = policy or CommunityEventIdentityPolicy.default()
    text = value if isinstance(value, str) else ""
    if reject_control_characters(text) or any(ch.isspace() for ch in text):
        raise ValueError("unsafe_value")
    if "/" in text or "\\" in text:
        raise ValueError("invalid_format")
    if _URLISH_RE.match(text):
        raise ValueError("unsafe_value")
    if len(text) < active.event_id_min_length:
        raise ValueError("too_short")
    if len(text) > active.event_id_max_length:
        raise ValueError("too_long")
    if not _EVENT_ID_RE.fullmatch(text):
        raise ValueError("invalid_format")
    if contains_secret_like_value(text):
        raise ValueError("unsafe_value")
    return text


def validate_installation_id_text(
    value: str,
    *,
    policy: CommunityEventIdentityPolicy | None = None,
) -> str:
    """Validate an optional future anonymous installation id (not generated here)."""

    # Same character/safety contract as event_id for now.
    return validate_event_id_text(value, policy=policy)


def build_event_identity_conflict_error(
    *,
    api_version: str,
    request_id: str | None = None,
    safe_event_reference: str | None = None,
) -> ApiErrorResponse:
    """Canonical conflict envelope — no fingerprints or raw event IDs."""

    details = None
    if safe_event_reference:
        details = {"safe_event_reference": safe_event_reference}
    return ApiErrorResponse.build(
        ERROR_EVENT_IDENTITY_CONFLICT,
        http_status=409,
        api_version=api_version,
        request_id=request_id,
        details=details,
    )

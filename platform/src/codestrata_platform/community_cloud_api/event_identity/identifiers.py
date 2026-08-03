"""Event-key and safe-reference helpers."""

from __future__ import annotations

import hashlib
import json

from codestrata_platform.community_cloud_api.event_identity.models import (
    CommunityEventIdentityPolicy,
    EventIdentityScope,
)


def build_event_key(
    scope: EventIdentityScope,
    *,
    policy: CommunityEventIdentityPolicy | None = None,
) -> str:
    """Build scoped event key: ``event:{sha256[:24]}``.

    Does not include timestamps, request IDs, IP, or payload content.
    """

    active = policy or CommunityEventIdentityPolicy.default()
    material = {
        "api_version": scope.api_version,
        "client_type": scope.client_type,
        "event_id": scope.event_id,
        "event_type": scope.event_type,
        "installation_id": scope.installation_id or "",
        "policy_token": active.policy_token,
    }
    text = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"event:{digest[:24]}"


def build_safe_event_reference(
    event_key: str,
    *,
    policy: CommunityEventIdentityPolicy | None = None,
) -> str:
    """Bounded non-reversible log reference derived from the event key digest."""

    active = policy or CommunityEventIdentityPolicy.default()
    raw = (event_key or "").strip()
    if raw.startswith("event:"):
        digest = raw[len("event:") :]
    else:
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    hex_part = "".join(ch for ch in digest.lower() if ch in "0123456789abcdef")
    if len(hex_part) < active.safe_log_identifier_length:
        hex_part = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"evt-{hex_part[: active.safe_log_identifier_length]}"

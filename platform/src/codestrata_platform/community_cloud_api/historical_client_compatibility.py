"""Historical client-record compatibility helpers (Slice 12.4).

Active emission, current API ingestion, and active storage projection reject
retired ``cursor_extension`` clients. These helpers exist only for reading and
validating previously accepted schema 1.0 records and stored metadata.

Never use these helpers to construct new active envelopes or S3 objects.
"""

from __future__ import annotations

from typing import Any

from codestrata_platform.community_cloud_api.ai_usage.enums import (
    HISTORICAL_AI_USAGE_CLIENTS,
    SCHEMA_AI_USAGE_CLIENTS,
)
from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest
from codestrata_platform.community_cloud_api.extension_events.enums import (
    HISTORICAL_EXTENSION_CLIENTS,
    SCHEMA_EXTENSION_CLIENTS,
)
from codestrata_platform.community_cloud_api.extension_events.models import (
    ExtensionEventRequest,
)
from codestrata_platform.community_cloud_api.retired_clients import (
    REASON_HISTORICAL_CLIENT_RECORD,
    REASON_RETIRED_CLIENT,
    REASON_UNSUPPORTED_ACTIVE_CLIENT,
    CommunityRetiredClientPolicy,
    default_retired_client_policy,
)

COMPATIBILITY_MODE_HISTORICAL_READ = "historical_read"
COMPATIBILITY_MODE_ACTIVE_REJECT = "active_reject"


def is_historical_extension_client(client_type: str) -> bool:
    return (client_type or "").strip() in HISTORICAL_EXTENSION_CLIENTS


def is_schema_extension_client(client_type: str) -> bool:
    return (client_type or "").strip() in SCHEMA_EXTENSION_CLIENTS


def is_historical_ai_usage_client(client_type: str) -> bool:
    return (client_type or "").strip() in HISTORICAL_AI_USAGE_CLIENTS


def is_schema_ai_usage_client(client_type: str) -> bool:
    return (client_type or "").strip() in SCHEMA_AI_USAGE_CLIENTS


def deserialize_historical_extension_event_payload(
    payload: dict[str, Any],
) -> ExtensionEventRequest:
    """Deserialize a previously accepted extension_event source payload.

    Uses schema 1.0 request models (Approach A). Does not authorize current
    ingestion or active projection.
    """

    return ExtensionEventRequest.model_validate(dict(payload))


def deserialize_historical_ai_usage_payload(payload: dict[str, Any]) -> AiUsageRequest:
    """Deserialize a previously accepted ai_usage source payload."""

    return AiUsageRequest.model_validate(dict(payload))


def historical_client_type_metadata_is_valid(
    client_type: str,
    *,
    policy: CommunityRetiredClientPolicy | None = None,
) -> bool:
    """Return True when stored ``codestrata-client-type`` is historically valid.

    Active clients and the retired historical Cursor value are accepted.
    Unknown values are rejected. Does not authorize new metadata emission.
    """

    active = policy or default_retired_client_policy()
    text = (client_type or "").strip()
    if not text:
        return False
    if text in SCHEMA_EXTENSION_CLIENTS or text in SCHEMA_AI_USAGE_CLIENTS:
        if active.is_retired_client(text):
            return active.allows_historical_storage_validation(text)
        return True
    return False


def active_client_rejection_reason(
    client_type: str,
    *,
    policy: CommunityRetiredClientPolicy | None = None,
) -> str:
    """Bounded reason code for rejecting a client on an active path.

    Never echoes the raw client value.
    """

    active = policy or default_retired_client_policy()
    if active.is_retired_client(client_type):
        return REASON_RETIRED_CLIENT
    return REASON_UNSUPPORTED_ACTIVE_CLIENT


def historical_compatibility_diagnostics(
    *,
    active_client_supported: bool,
    historical_client_supported: bool,
    compatibility_mode: str,
    policy: CommunityRetiredClientPolicy | None = None,
) -> dict[str, Any]:
    """Privacy-safe diagnostics for active vs historical client handling."""

    active = policy or default_retired_client_policy()
    return {
        "active_client_supported": active_client_supported,
        "compatibility_mode": compatibility_mode,
        "historical_client_supported": historical_client_supported,
        "reason_code": (
            REASON_HISTORICAL_CLIENT_RECORD
            if historical_client_supported
            else REASON_RETIRED_CLIENT
        ),
        "retirement_policy_version": active.policy_version,
    }

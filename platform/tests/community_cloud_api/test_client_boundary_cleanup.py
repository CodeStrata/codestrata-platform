"""Slice 12.4 — active vs historical Community client vocabulary."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from codestrata_platform.community_cloud_api.ai_usage.enums import (
    ACTIVE_AI_USAGE_CLIENTS,
    ALLOWED_AI_USAGE_CLIENTS,
    HISTORICAL_AI_USAGE_CLIENTS,
    SCHEMA_AI_USAGE_CLIENTS,
)
from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest
from codestrata_platform.community_cloud_api.ai_usage.validation import (
    validate_ai_usage_semantics,
)
from codestrata_platform.community_cloud_api.authentication.models import (
    ACTIVE_CLIENT_TYPES,
    ALLOWED_CLIENT_TYPES,
    CLIENT_TYPE_CURSOR,
    HISTORICAL_CLIENT_TYPES,
)
from codestrata_platform.community_cloud_api.data_lake.canonical_json import (
    serialize_canonical_raw_json,
)
from codestrata_platform.community_cloud_api.data_lake.envelope_serialization import (
    deserialize_data_lake_envelope,
)
from codestrata_platform.community_cloud_api.data_lake.envelopes import build_envelope
from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    PartitionProjectionError,
    project_extension_event_storage_object,
)
from codestrata_platform.community_cloud_api.extension_events.enums import (
    ACTIVE_EXTENSION_CLIENTS,
    ALLOWED_EXTENSION_CLIENTS,
    CURSOR_EXTENSION_CLIENT,
    HISTORICAL_EXTENSION_CLIENTS,
    SCHEMA_EXTENSION_CLIENTS,
)
from codestrata_platform.community_cloud_api.extension_events.models import (
    ExtensionEventRequest,
)
from codestrata_platform.community_cloud_api.extension_events.validation import (
    validate_extension_event_semantics,
)
from codestrata_platform.community_cloud_api.historical_client_compatibility import (
    active_client_rejection_reason,
    deserialize_historical_extension_event_payload,
    historical_client_type_metadata_is_valid,
    historical_compatibility_diagnostics,
)
from codestrata_platform.community_cloud_api.retired_clients import (
    COMMUNITY_RETIRED_CLIENT_POLICY_URN,
    REASON_RETIRED_CLIENT,
    default_retired_client_policy,
)

from .extension_event_helpers import valid_extension_event_body
from .ai_usage_helpers import valid_ai_usage_body


def test_active_vocabularies_exclude_cursor() -> None:
    assert CURSOR_EXTENSION_CLIENT not in ACTIVE_EXTENSION_CLIENTS
    assert CURSOR_EXTENSION_CLIENT not in ALLOWED_EXTENSION_CLIENTS
    assert CURSOR_EXTENSION_CLIENT in HISTORICAL_EXTENSION_CLIENTS
    assert CURSOR_EXTENSION_CLIENT in SCHEMA_EXTENSION_CLIENTS

    assert "cursor_extension" not in ACTIVE_AI_USAGE_CLIENTS
    assert "cursor_extension" not in ALLOWED_AI_USAGE_CLIENTS
    assert "cursor_extension" in HISTORICAL_AI_USAGE_CLIENTS
    assert "cursor_extension" in SCHEMA_AI_USAGE_CLIENTS

    assert CLIENT_TYPE_CURSOR not in ACTIVE_CLIENT_TYPES
    assert CLIENT_TYPE_CURSOR not in ALLOWED_CLIENT_TYPES
    assert CLIENT_TYPE_CURSOR in HISTORICAL_CLIENT_TYPES


def test_retired_client_policy_defaults() -> None:
    policy = default_retired_client_policy()
    assert policy.policy_token == COMMUNITY_RETIRED_CLIENT_POLICY_URN
    assert policy.active_emission_allowed is False
    assert policy.current_ingestion_allowed is False
    assert policy.historical_deserialization_allowed is True
    assert policy.rewrite_required is False
    assert policy.migration_required is False
    dumped = policy.to_stable_dict()
    assert "retired_client" not in dumped
    assert "cursor_extension" not in str(dumped)


def test_current_ingestion_rejects_cursor_extension_event() -> None:
    body = valid_extension_event_body()
    body["client"] = {
        "name": "cursor_extension",
        "version": "0.2.0",
        "editor": "cursor",
        "editor_version": "0.45.0",
        "platform": "darwin",
    }
    model = ExtensionEventRequest.model_validate(body)
    errors = validate_extension_event_semantics(model)
    assert any(err.field == "client.name" for err in errors)


def test_current_ingestion_rejects_cursor_ai_usage() -> None:
    body = valid_ai_usage_body()
    body["client"] = {
        "name": "cursor_extension",
        "version": "0.2.0",
        "platform": "darwin",
    }
    model = AiUsageRequest.model_validate(body)
    errors = validate_ai_usage_semantics(model)
    assert any(err.field == "client.name" for err in errors)


def test_historical_extension_payload_deserializes_and_active_projection_rejects() -> None:
    body = valid_extension_event_body()
    body["client"] = {
        "name": "cursor_extension",
        "version": "0.2.0",
        "editor": "cursor",
        "editor_version": "0.45.0",
        "platform": "darwin",
    }
    request = deserialize_historical_extension_event_payload(body)
    payload = request.to_stable_dict()
    envelope = build_envelope(
        event_stream="extension_event",
        schema_name="community-extension-event",
        schema_version="1.0",
        policy_id="community-extension-event-policy:1.0",
        event_key="event:hist-cursor-ext-0001",
        safe_event_reference="evt-histcursor0001",
        accepted_at="2026-08-01T00:00:00Z",
        client_type="cursor_extension",
        payload=payload,
    )
    # Historical deserialize round-trip (schema 1.0 + revalidate).
    canonical = serialize_canonical_raw_json(envelope)
    restored = deserialize_data_lake_envelope(canonical.data)
    assert restored.client.client_type == "cursor_extension"

    with pytest.raises(PartitionProjectionError) as excinfo:
        project_extension_event_storage_object(envelope)
    assert excinfo.value.code == "invalid_client_type"

    assert historical_client_type_metadata_is_valid("cursor_extension")
    assert active_client_rejection_reason("cursor_extension") == REASON_RETIRED_CLIENT
    diag = historical_compatibility_diagnostics(
        active_client_supported=False,
        historical_client_supported=True,
        compatibility_mode="historical_read",
    )
    assert "cursor_extension" not in str(diag)


def test_unknown_client_rejected_by_schema() -> None:
    body = valid_extension_event_body()
    body["client"] = {
        "name": "mystery_extension",
        "version": "0.2.0",
        "editor": "vscode",
        "editor_version": "1.85.0",
        "platform": "darwin",
    }
    with pytest.raises(ValidationError):
        ExtensionEventRequest.model_validate(body)

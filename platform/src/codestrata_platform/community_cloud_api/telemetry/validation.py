"""Telemetry semantic validation helpers (Slice 7.7)."""

from __future__ import annotations

from collections.abc import Sequence

from codestrata_platform.community_cloud_api.telemetry.models import (
    TelemetryIngestionRequest,
)
from codestrata_platform.community_cloud_api.telemetry.policy import (
    COMMUNITY_TELEMETRY_SCHEMA_VERSION,
    CommunityTelemetryPolicy,
    default_telemetry_policy,
)
from codestrata_platform.community_cloud_api.validation.errors import (
    FIELD_INVALID_ENUM,
    FIELD_INVALID_FORMAT,
    FIELD_TOO_LARGE,
    FIELD_UNKNOWN,
    FIELD_UNSAFE_VALUE,
    field_error,
)
from codestrata_platform.community_cloud_api.validation.models import (
    CommunityApiRequestModel,
    ValidationFieldError,
)


def validate_telemetry_semantics(
    model: CommunityApiRequestModel,
    *,
    policy: CommunityTelemetryPolicy | None = None,
) -> Sequence[ValidationFieldError]:
    """Fail-closed semantic checks beyond structural pydantic validation."""

    active = policy or default_telemetry_policy()
    if not isinstance(model, TelemetryIngestionRequest):
        return (field_error("request", FIELD_INVALID_FORMAT),)

    errors: list[ValidationFieldError] = []

    if model.schema_version != active.telemetry_schema_version:
        errors.append(field_error("schema_version", FIELD_INVALID_ENUM))

    if model.event_type not in active.allowed_event_types:
        errors.append(field_error("event_type", FIELD_INVALID_ENUM))

    if model.client.name not in active.allowed_client_names:
        errors.append(field_error("client.name", FIELD_INVALID_ENUM))

    if model.installation_id is not None and not active.allow_installation_id:
        errors.append(field_error("installation_id", FIELD_UNKNOWN))

    if model.occurred_at is not None and not active.allow_occurred_at:
        errors.append(field_error("occurred_at", FIELD_UNKNOWN))

    if model.properties is not None:
        props = model.properties.to_stable_dict()
        # Drop None values for count.
        present = {key: value for key, value in props.items() if value is not None}
        if len(present) > active.maximum_property_count:
            errors.append(field_error("properties", FIELD_TOO_LARGE))
        for key in present:
            if key not in active.allowed_property_fields:
                errors.append(field_error(f"properties.{key}", FIELD_UNKNOWN))
            if key in active.forbidden_field_names:
                errors.append(field_error(f"properties.{key}", FIELD_UNSAFE_VALUE))

    # Reject forbidden field names if they somehow appear in the stable dump.
    dumped = model.to_stable_dict()
    for key in dumped:
        if key in active.forbidden_field_names:
            errors.append(field_error(key, FIELD_UNSAFE_VALUE))

    # Stable schema constant self-check (defense in depth).
    if COMMUNITY_TELEMETRY_SCHEMA_VERSION != "1.0":
        errors.append(field_error("schema_version", FIELD_INVALID_ENUM))

    # Deduplicate by field+code.
    unique: dict[tuple[str, str], ValidationFieldError] = {}
    for item in errors:
        unique[(item.field, item.code)] = item
    return tuple(
        sorted(unique.values(), key=lambda err: (err.field, err.code, err.message))
    )

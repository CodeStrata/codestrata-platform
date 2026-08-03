"""Strict telemetry request models (Slice 7.7)."""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import Field, StrictInt, StrictStr, field_validator

from codestrata_platform.community_cloud_api.telemetry.enums import (
    TelemetryClientName,
    TelemetryDurationBucket,
    TelemetryEventType,
    TelemetryOutcome,
)
from codestrata_platform.community_cloud_api.telemetry.policy import (
    COMMUNITY_TELEMETRY_SCHEMA_VERSION,
    default_telemetry_policy,
)
from codestrata_platform.community_cloud_api.validation.models import (
    CommunityApiRequestModel,
)
from codestrata_platform.community_cloud_api.validation.sanitization import (
    contains_secret_like_value,
    reject_control_characters,
)
from codestrata_platform.community_cloud_api.validation.schema import (
    ApiClientVersion,
    ApiEventId,
    ApiInstallationId,
    ApiPlatformName,
)

_RFC3339_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?(?:Z|[+-]\d{2}:\d{2})$"
)
_SAFE_LABEL_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
_MAX_FLAGS = 8


def _require_safe_bounded_label(value: str, *, max_length: int) -> str:
    if reject_control_characters(value) or any(ch.isspace() for ch in value):
        raise ValueError("unsafe_value")
    if len(value) > max_length:
        raise ValueError("too_long")
    if not _SAFE_LABEL_RE.fullmatch(value):
        raise ValueError("invalid_format")
    if contains_secret_like_value(value):
        raise ValueError("unsafe_value")
    # Reject obvious URLs / paths in property labels.
    lower = value.lower()
    if "://" in lower or lower.startswith("file:"):
        raise ValueError("unsafe_value")
    if "/" in value or "\\" in value:
        raise ValueError("unsafe_value")
    return value


class TelemetryClient(CommunityApiRequestModel):
    """Bounded anonymous client descriptor — no host/user/repo identity."""

    name: StrictStr = Field(min_length=1, max_length=64)
    version: ApiClientVersion
    platform: ApiPlatformName

    @field_validator("name")
    @classmethod
    def _name_allowlisted(cls, value: str) -> str:
        policy = default_telemetry_policy()
        text = value.strip()
        if text not in policy.allowed_client_names:
            raise ValueError("invalid_enum")
        return text


class TelemetryProperties(CommunityApiRequestModel):
    """Bounded allowlisted properties — no free-form metadata."""

    feature: StrictStr | None = Field(default=None, min_length=1, max_length=64)
    operation: StrictStr | None = Field(default=None, min_length=1, max_length=64)
    outcome: StrictStr | None = Field(default=None, min_length=1, max_length=32)
    duration_bucket: StrictStr | None = Field(default=None, min_length=1, max_length=32)
    count: Annotated[StrictInt, Field(ge=0, le=10_000)] | None = None
    flags: list[StrictStr] | None = Field(default=None, max_length=_MAX_FLAGS)

    @field_validator("feature", "operation")
    @classmethod
    def _safe_labels(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _require_safe_bounded_label(value, max_length=64)

    @field_validator("outcome")
    @classmethod
    def _outcome_vocab(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = _require_safe_bounded_label(value, max_length=32)
        if text not in {item.value for item in TelemetryOutcome}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("duration_bucket")
    @classmethod
    def _duration_vocab(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = _require_safe_bounded_label(value, max_length=32)
        if text not in {item.value for item in TelemetryDurationBucket}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("flags")
    @classmethod
    def _flags_safe(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        if len(value) > _MAX_FLAGS:
            raise ValueError("too_long")
        cleaned = [_require_safe_bounded_label(item, max_length=32) for item in value]
        return cleaned


class TelemetryIngestionRequest(CommunityApiRequestModel):
    """Privacy-first single-event telemetry envelope."""

    schema_version: Literal["1.0"]  # type: ignore[valid-type]
    event_id: ApiEventId
    event_type: StrictStr = Field(min_length=1, max_length=64)
    client: TelemetryClient
    installation_id: ApiInstallationId | None = None
    occurred_at: StrictStr | None = Field(default=None, min_length=1, max_length=64)
    properties: TelemetryProperties | None = None

    @field_validator("event_type")
    @classmethod
    def _event_type_allowlisted(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in TelemetryEventType}:
            raise ValueError("invalid_enum")
        if contains_secret_like_value(text):
            raise ValueError("unsafe_value")
        return text

    @field_validator("occurred_at")
    @classmethod
    def _occurred_at_rfc3339(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if reject_control_characters(value) or any(ch.isspace() for ch in value):
            raise ValueError("unsafe_value")
        if not _RFC3339_RE.fullmatch(value):
            raise ValueError("invalid_format")
        if contains_secret_like_value(value):
            raise ValueError("unsafe_value")
        return value

    def fingerprint_payload(self) -> dict[str, Any]:
        """Material used for payload fingerprinting.

        Includes ``event_id`` because the identity policy forbids excluding it
        from fingerprints; ``event_key`` still owns scoped logical identity.
        ``occurred_at`` participates when present (client-submitted content).
        Transport ``request_id`` is never present on this model.
        """

        return self.to_stable_dict()

    def schema_version_value(self) -> str:
        return COMMUNITY_TELEMETRY_SCHEMA_VERSION

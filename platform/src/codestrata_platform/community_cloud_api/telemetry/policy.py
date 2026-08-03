"""Community Cloud telemetry policy (Slice 7.7)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.telemetry.enums import (
    TelemetryClientName,
    TelemetryDurationBucket,
    TelemetryEventType,
    TelemetryOutcome,
)

COMMUNITY_TELEMETRY_SCHEMA_VERSION = "1.0"
COMMUNITY_TELEMETRY_POLICY_ID = "community-telemetry-policy"
COMMUNITY_TELEMETRY_POLICY_VERSION = "1.0"
COMMUNITY_TELEMETRY_POLICY_URN = (
    f"{COMMUNITY_TELEMETRY_POLICY_ID}:{COMMUNITY_TELEMETRY_POLICY_VERSION}"
)

ALLOWED_PROPERTY_FIELDS: tuple[str, ...] = (
    "count",
    "duration_bucket",
    "feature",
    "flags",
    "operation",
    "outcome",
)

FORBIDDEN_FIELD_NAMES: tuple[str, ...] = (
    "api_key",
    "args",
    "command",
    "command_args",
    "credential",
    "email",
    "exception",
    "filepath",
    "filename",
    "file_name",
    "git_remote",
    "hostname",
    "password",
    "private_key",
    "prompt",
    "repository_name",
    "repository_url",
    "secret",
    "source_code",
    "stack_trace",
    "token",
    "username",
    "user_email",
)


@dataclass(frozen=True, slots=True)
class CommunityTelemetryPolicy:
    """Deterministic privacy-first telemetry policy."""

    policy_id: str = COMMUNITY_TELEMETRY_POLICY_ID
    policy_version: str = COMMUNITY_TELEMETRY_POLICY_VERSION
    telemetry_schema_version: str = COMMUNITY_TELEMETRY_SCHEMA_VERSION
    allowed_event_types: tuple[str, ...] = tuple(
        sorted(item.value for item in TelemetryEventType)
    )
    allowed_client_names: tuple[str, ...] = tuple(
        sorted(item.value for item in TelemetryClientName)
    )
    allowed_property_fields: tuple[str, ...] = ALLOWED_PROPERTY_FIELDS
    allow_installation_id: bool = True
    allow_occurred_at: bool = True
    maximum_property_count: int = 6
    maximum_string_length: int = 64
    maximum_count: int = 10_000
    duration_bucket_vocabulary: tuple[str, ...] = tuple(
        sorted(item.value for item in TelemetryDurationBucket)
    )
    outcome_vocabulary: tuple[str, ...] = tuple(
        sorted(item.value for item in TelemetryOutcome)
    )
    forbidden_field_names: tuple[str, ...] = FORBIDDEN_FIELD_NAMES
    limitations: tuple[str, ...] = (
        "no_production_event_store",
        "no_exactly_once_guarantee",
        "sink_and_identity_record_not_atomic",
        "unauthenticated_endpoint",
        "no_rate_limiting",
        "anonymous_technical_events_only",
    )

    def __post_init__(self) -> None:
        if self.policy_id != COMMUNITY_TELEMETRY_POLICY_ID:
            raise ValueError("unsupported telemetry policy id")
        if self.policy_version != COMMUNITY_TELEMETRY_POLICY_VERSION:
            raise ValueError("unsupported telemetry policy version")
        if self.telemetry_schema_version != COMMUNITY_TELEMETRY_SCHEMA_VERSION:
            raise ValueError("unsupported telemetry schema version in policy")
        if self.maximum_property_count < 1 or self.maximum_count < 1:
            raise ValueError("invalid telemetry bounds")
        object.__setattr__(
            self, "allowed_event_types", tuple(sorted(self.allowed_event_types))
        )
        object.__setattr__(
            self, "allowed_client_names", tuple(sorted(self.allowed_client_names))
        )
        object.__setattr__(
            self, "allowed_property_fields", tuple(sorted(self.allowed_property_fields))
        )
        object.__setattr__(
            self, "forbidden_field_names", tuple(sorted(set(self.forbidden_field_names)))
        )
        object.__setattr__(self, "limitations", tuple(sorted(self.limitations)))

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    @classmethod
    def default(cls) -> CommunityTelemetryPolicy:
        return cls()

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "allow_installation_id": self.allow_installation_id,
            "allow_occurred_at": self.allow_occurred_at,
            "allowed_client_names": list(self.allowed_client_names),
            "allowed_event_types": list(self.allowed_event_types),
            "allowed_property_fields": list(self.allowed_property_fields),
            "duration_bucket_vocabulary": list(self.duration_bucket_vocabulary),
            "forbidden_field_names": list(self.forbidden_field_names),
            "limitations": list(self.limitations),
            "maximum_count": self.maximum_count,
            "maximum_property_count": self.maximum_property_count,
            "maximum_string_length": self.maximum_string_length,
            "outcome_vocabulary": list(self.outcome_vocabulary),
            "policy_id": self.policy_id,
            "policy_token": self.policy_token,
            "policy_version": self.policy_version,
            "telemetry_schema_version": self.telemetry_schema_version,
        }


def default_telemetry_policy() -> CommunityTelemetryPolicy:
    return CommunityTelemetryPolicy.default()

"""Structured logging models for Community Cloud API."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


COMMUNITY_LOGGING_POLICY_ID = "community-logging-policy"
COMMUNITY_LOGGING_POLICY_VERSION = "1.0"
COMMUNITY_LOGGING_POLICY_URN = (
    f"{COMMUNITY_LOGGING_POLICY_ID}:{COMMUNITY_LOGGING_POLICY_VERSION}"
)


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class LogEventType(str, Enum):
    REQUEST_RECEIVED = "request_received"
    REQUEST_COMPLETED = "request_completed"
    REQUEST_FAILED = "request_failed"
    VALIDATION_FAILED = "validation_failed"
    PAYLOAD_REJECTED = "payload_rejected"
    HEALTH_CHECKED = "health_checked"
    # Additive under community-logging-policy:1.0 (Slice 7.7).
    TELEMETRY_RECEIVED = "telemetry_received"
    TELEMETRY_ACCEPTED = "telemetry_accepted"
    TELEMETRY_RETRY = "telemetry_retry"
    TELEMETRY_CONFLICT = "telemetry_conflict"
    TELEMETRY_REJECTED = "telemetry_rejected"
    # Additive under community-logging-policy:1.0 (Slice 7.8).
    ASSESSMENT_METADATA_RECEIVED = "assessment_metadata_received"
    ASSESSMENT_METADATA_ACCEPTED = "assessment_metadata_accepted"
    ASSESSMENT_METADATA_RETRY = "assessment_metadata_retry"
    ASSESSMENT_METADATA_CONFLICT = "assessment_metadata_conflict"
    ASSESSMENT_METADATA_REJECTED = "assessment_metadata_rejected"
    # Additive under community-logging-policy:1.0 (Slice 7.9).
    CLI_EVENT_RECEIVED = "cli_event_received"
    CLI_EVENT_ACCEPTED = "cli_event_accepted"
    CLI_EVENT_RETRY = "cli_event_retry"
    CLI_EVENT_CONFLICT = "cli_event_conflict"
    CLI_EVENT_REJECTED = "cli_event_rejected"
    # Additive under community-logging-policy:1.0 (Slice 7.10).
    EXTENSION_EVENT_RECEIVED = "extension_event_received"
    EXTENSION_EVENT_ACCEPTED = "extension_event_accepted"
    EXTENSION_EVENT_RETRY = "extension_event_retry"
    EXTENSION_EVENT_CONFLICT = "extension_event_conflict"
    EXTENSION_EVENT_REJECTED = "extension_event_rejected"
    # Additive under community-logging-policy:1.0 (Slice 7.11).
    AI_USAGE_RECEIVED = "ai_usage_received"
    AI_USAGE_ACCEPTED = "ai_usage_accepted"
    AI_USAGE_RETRY = "ai_usage_retry"
    AI_USAGE_CONFLICT = "ai_usage_conflict"
    AI_USAGE_REJECTED = "ai_usage_rejected"
    # Additive under community-logging-policy:1.0 (Slice 7.12).
    RATE_LIMIT_ALLOWED = "rate_limit_allowed"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    RATE_LIMIT_UNAVAILABLE = "rate_limit_unavailable"
    # Additive under community-logging-policy:1.0 (Slice 7.13).
    AUTHENTICATION_SUCCEEDED = "authentication_succeeded"
    AUTHENTICATION_FAILED = "authentication_failed"
    AUTHENTICATION_UNAVAILABLE = "authentication_unavailable"
    AUTHORIZATION_DENIED = "authorization_denied"
    # Additive under community-logging-policy:1.0 (Slice 8.2). Not emitted
    # from any endpoint in this slice — reserved for a future wiring slice.
    DATA_LAKE_STORE_ATTEMPTED = "data_lake_store_attempted"
    DATA_LAKE_STORED = "data_lake_stored"
    DATA_LAKE_ALREADY_EXISTS = "data_lake_already_exists"
    DATA_LAKE_CONFLICT = "data_lake_conflict"
    DATA_LAKE_UNAVAILABLE = "data_lake_unavailable"
    DATA_LAKE_REJECTED = "data_lake_rejected"


_EVENT_LEVELS: dict[LogEventType, LogLevel] = {
    LogEventType.REQUEST_RECEIVED: LogLevel.INFO,
    LogEventType.REQUEST_COMPLETED: LogLevel.INFO,
    LogEventType.REQUEST_FAILED: LogLevel.WARNING,
    LogEventType.VALIDATION_FAILED: LogLevel.WARNING,
    LogEventType.PAYLOAD_REJECTED: LogLevel.WARNING,
    LogEventType.HEALTH_CHECKED: LogLevel.INFO,
    LogEventType.TELEMETRY_RECEIVED: LogLevel.INFO,
    LogEventType.TELEMETRY_ACCEPTED: LogLevel.INFO,
    LogEventType.TELEMETRY_RETRY: LogLevel.INFO,
    LogEventType.TELEMETRY_CONFLICT: LogLevel.WARNING,
    LogEventType.TELEMETRY_REJECTED: LogLevel.WARNING,
    LogEventType.ASSESSMENT_METADATA_RECEIVED: LogLevel.INFO,
    LogEventType.ASSESSMENT_METADATA_ACCEPTED: LogLevel.INFO,
    LogEventType.ASSESSMENT_METADATA_RETRY: LogLevel.INFO,
    LogEventType.ASSESSMENT_METADATA_CONFLICT: LogLevel.WARNING,
    LogEventType.ASSESSMENT_METADATA_REJECTED: LogLevel.WARNING,
    LogEventType.CLI_EVENT_RECEIVED: LogLevel.INFO,
    LogEventType.CLI_EVENT_ACCEPTED: LogLevel.INFO,
    LogEventType.CLI_EVENT_RETRY: LogLevel.INFO,
    LogEventType.CLI_EVENT_CONFLICT: LogLevel.WARNING,
    LogEventType.CLI_EVENT_REJECTED: LogLevel.WARNING,
    LogEventType.EXTENSION_EVENT_RECEIVED: LogLevel.INFO,
    LogEventType.EXTENSION_EVENT_ACCEPTED: LogLevel.INFO,
    LogEventType.EXTENSION_EVENT_RETRY: LogLevel.INFO,
    LogEventType.EXTENSION_EVENT_CONFLICT: LogLevel.WARNING,
    LogEventType.EXTENSION_EVENT_REJECTED: LogLevel.WARNING,
    LogEventType.AI_USAGE_RECEIVED: LogLevel.INFO,
    LogEventType.AI_USAGE_ACCEPTED: LogLevel.INFO,
    LogEventType.AI_USAGE_RETRY: LogLevel.INFO,
    LogEventType.AI_USAGE_CONFLICT: LogLevel.WARNING,
    LogEventType.AI_USAGE_REJECTED: LogLevel.WARNING,
    LogEventType.RATE_LIMIT_ALLOWED: LogLevel.INFO,
    LogEventType.RATE_LIMIT_EXCEEDED: LogLevel.WARNING,
    LogEventType.RATE_LIMIT_UNAVAILABLE: LogLevel.WARNING,
    LogEventType.AUTHENTICATION_SUCCEEDED: LogLevel.INFO,
    LogEventType.AUTHENTICATION_FAILED: LogLevel.WARNING,
    LogEventType.AUTHENTICATION_UNAVAILABLE: LogLevel.WARNING,
    LogEventType.AUTHORIZATION_DENIED: LogLevel.WARNING,
    LogEventType.DATA_LAKE_STORE_ATTEMPTED: LogLevel.INFO,
    LogEventType.DATA_LAKE_STORED: LogLevel.INFO,
    LogEventType.DATA_LAKE_ALREADY_EXISTS: LogLevel.INFO,
    LogEventType.DATA_LAKE_CONFLICT: LogLevel.WARNING,
    LogEventType.DATA_LAKE_UNAVAILABLE: LogLevel.WARNING,
    LogEventType.DATA_LAKE_REJECTED: LogLevel.WARNING,
}


def level_for_event(event_type: LogEventType) -> LogLevel:
    return _EVENT_LEVELS.get(event_type, LogLevel.INFO)


@dataclass(frozen=True, slots=True)
class StructuredLogEvent:
    """Canonical structured log record — allowlisted fields only."""

    event_type: LogEventType
    level: LogLevel
    api_version: str
    method: str
    route: str
    request_id: str
    policy_version: str = COMMUNITY_LOGGING_POLICY_URN
    status_code: int | None = None
    duration_ms: int | None = None
    error_code: str | None = None
    route_name: str | None = None
    client_host: str | None = None
    event_seq: int | None = None
    # Optional ISO timestamp only when an injectable clock provides it.
    timestamp: str | None = None
    # Explicit safe event-identity fields only (never raw event_id / fingerprints).
    safe_event_reference: str | None = None
    retry_status: str | None = None
    source_event_type: str | None = None
    identity_policy_version: str | None = None
    telemetry_schema_version: str | None = None
    telemetry_policy_version: str | None = None
    metadata_schema_version: str | None = None
    metadata_policy_version: str | None = None
    client_type: str | None = None
    assessment_status: str | None = None
    cli_schema_version: str | None = None
    cli_policy_version: str | None = None
    canonical_operation: str | None = None
    lifecycle: str | None = None
    result: str | None = None
    extension_schema_version: str | None = None
    extension_policy_version: str | None = None
    ai_schema_version: str | None = None
    ai_policy_version: str | None = None
    canonical_capability: str | None = None
    outcome: str | None = None
    # Rate-limit safe fields (Slice 7.12) — never raw IP / full scope key.
    rate_limit_policy_id: str | None = None
    rate_limit_limit: int | None = None
    rate_limit_remaining: int | None = None
    retry_after_seconds: int | None = None
    safe_scope_reference: str | None = None
    # Authentication safe fields (Slice 7.13).
    authentication_policy_id: str | None = None
    authentication_reason: str | None = None
    verifier_status: str | None = None
    safe_client_reference: str | None = None
    # Community Data Lake storage safe fields (Slice 8.2). Not emitted from
    # any endpoint in this slice — reserved for a future wiring slice.
    storage_status: str | None = None
    data_lake_policy_version: str | None = None
    data_lake_envelope_schema_version: str | None = None
    event_stream: str | None = None
    safe_object_reference: str | None = None

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "api_version": self.api_version,
            "event_type": self.event_type.value,
            "level": self.level.value,
            "method": self.method,
            "policy_version": self.policy_version,
            "request_id": self.request_id,
            "route": self.route,
        }
        if self.assessment_status is not None:
            payload["assessment_status"] = self.assessment_status
        if self.ai_policy_version is not None:
            payload["ai_policy_version"] = self.ai_policy_version
        if self.ai_schema_version is not None:
            payload["ai_schema_version"] = self.ai_schema_version
        if self.authentication_policy_id is not None:
            payload["authentication_policy_id"] = self.authentication_policy_id
        if self.authentication_reason is not None:
            payload["authentication_reason"] = self.authentication_reason
        if self.canonical_capability is not None:
            payload["canonical_capability"] = self.canonical_capability
        if self.canonical_operation is not None:
            payload["canonical_operation"] = self.canonical_operation
        if self.cli_policy_version is not None:
            payload["cli_policy_version"] = self.cli_policy_version
        if self.cli_schema_version is not None:
            payload["cli_schema_version"] = self.cli_schema_version
        if self.client_host is not None:
            payload["client_host"] = self.client_host
        if self.client_type is not None:
            payload["client_type"] = self.client_type
        if self.data_lake_envelope_schema_version is not None:
            payload["data_lake_envelope_schema_version"] = self.data_lake_envelope_schema_version
        if self.data_lake_policy_version is not None:
            payload["data_lake_policy_version"] = self.data_lake_policy_version
        if self.duration_ms is not None:
            payload["duration_ms"] = int(self.duration_ms)
        if self.error_code is not None:
            payload["error_code"] = self.error_code
        if self.event_seq is not None:
            payload["event_seq"] = int(self.event_seq)
        if self.event_stream is not None:
            payload["event_stream"] = self.event_stream
        if self.extension_policy_version is not None:
            payload["extension_policy_version"] = self.extension_policy_version
        if self.extension_schema_version is not None:
            payload["extension_schema_version"] = self.extension_schema_version
        if self.identity_policy_version is not None:
            payload["identity_policy_version"] = self.identity_policy_version
        if self.lifecycle is not None:
            payload["lifecycle"] = self.lifecycle
        if self.metadata_policy_version is not None:
            payload["metadata_policy_version"] = self.metadata_policy_version
        if self.metadata_schema_version is not None:
            payload["metadata_schema_version"] = self.metadata_schema_version
        if self.outcome is not None:
            payload["outcome"] = self.outcome
        if self.rate_limit_limit is not None:
            payload["rate_limit_limit"] = int(self.rate_limit_limit)
        if self.rate_limit_policy_id is not None:
            payload["rate_limit_policy_id"] = self.rate_limit_policy_id
        if self.rate_limit_remaining is not None:
            payload["rate_limit_remaining"] = int(self.rate_limit_remaining)
        if self.result is not None:
            payload["result"] = self.result
        if self.retry_after_seconds is not None:
            payload["retry_after_seconds"] = int(self.retry_after_seconds)
        if self.retry_status is not None:
            payload["retry_status"] = self.retry_status
        if self.route_name is not None:
            payload["route_name"] = self.route_name
        if self.safe_client_reference is not None:
            payload["safe_client_reference"] = self.safe_client_reference
        if self.safe_event_reference is not None:
            payload["safe_event_reference"] = self.safe_event_reference
        if self.safe_object_reference is not None:
            payload["safe_object_reference"] = self.safe_object_reference
        if self.safe_scope_reference is not None:
            payload["safe_scope_reference"] = self.safe_scope_reference
        if self.source_event_type is not None:
            payload["source_event_type"] = self.source_event_type
        if self.status_code is not None:
            payload["status_code"] = int(self.status_code)
        if self.storage_status is not None:
            payload["storage_status"] = self.storage_status
        if self.telemetry_policy_version is not None:
            payload["telemetry_policy_version"] = self.telemetry_policy_version
        if self.telemetry_schema_version is not None:
            payload["telemetry_schema_version"] = self.telemetry_schema_version
        if self.timestamp is not None:
            payload["timestamp"] = self.timestamp
        if self.verifier_status is not None:
            payload["verifier_status"] = self.verifier_status
        return {key: payload[key] for key in sorted(payload)}


@dataclass(frozen=True, slots=True)
class CommunityLoggingPolicy:
    """Deterministic logging policy — no backends or shipping."""

    policy_version: str = COMMUNITY_LOGGING_POLICY_URN
    max_field_length: int = 128
    max_request_id_length: int = 64
    include_client_host: bool = True
    include_timestamps: bool = False
    allowed_event_types: tuple[str, ...] = tuple(
        sorted(item.value for item in LogEventType)
    )

    def __post_init__(self) -> None:
        if self.policy_version != COMMUNITY_LOGGING_POLICY_URN:
            raise ValueError("unsupported community logging policy version")
        if self.max_field_length < 8 or self.max_request_id_length < 8:
            raise ValueError("field length bounds too small")
        object.__setattr__(
            self,
            "allowed_event_types",
            tuple(sorted(self.allowed_event_types)),
        )

    @classmethod
    def default(cls) -> CommunityLoggingPolicy:
        return cls()

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "allowed_event_types": list(self.allowed_event_types),
            "include_client_host": self.include_client_host,
            "include_timestamps": self.include_timestamps,
            "max_field_length": self.max_field_length,
            "max_request_id_length": self.max_request_id_length,
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True, slots=True)
class LoggingDiagnostic:
    """Safe internal diagnostic — never includes payloads or headers."""

    event_type: str
    error_code: str | None
    route_name: str | None

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"event_type": self.event_type}
        if self.error_code is not None:
            payload["error_code"] = self.error_code
        if self.route_name is not None:
            payload["route_name"] = self.route_name
        return {key: payload[key] for key in sorted(payload)}


def filter_allowlisted_fields(
    values: Mapping[str, Any],
    *,
    allowed: frozenset[str],
) -> dict[str, Any]:
    return {key: values[key] for key in sorted(values) if key in allowed}

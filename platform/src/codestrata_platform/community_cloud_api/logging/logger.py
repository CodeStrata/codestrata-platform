"""Fail-safe Community Cloud structured logger."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

from codestrata_platform.community_cloud_api.logging.context import (
    LoggingContext,
    SequenceClock,
    SequenceRequestIdFactory,
)
from codestrata_platform.community_cloud_api.logging.formatter import format_log_event
from codestrata_platform.community_cloud_api.logging.models import (
    COMMUNITY_LOGGING_POLICY_URN,
    CommunityLoggingPolicy,
    LogEventType,
    LogLevel,
    StructuredLogEvent,
    level_for_event,
)
from codestrata_platform.community_cloud_api.logging.policy import (
    assert_supported_logging_policy,
    default_logging_policy,
)
from codestrata_platform.community_cloud_api.logging.sanitization import (
    sanitize_error_code,
    assert_safe_event_log_fields,
)


class LogSink(Protocol):
    def write(self, line: str) -> None: ...


@dataclass
class MemoryLogSink:
    """In-memory sink for tests — stores formatted JSON lines."""

    lines: list[str] = field(default_factory=list)

    def write(self, line: str) -> None:
        self.lines.append(line if line.endswith("\n") else line + "\n")

    def events(self) -> list[dict[str, object]]:
        import json

        return [json.loads(line) for line in self.lines]


class NullLogSink:
    def write(self, line: str) -> None:
        _ = line


@dataclass
class CommunityCloudLogger:
    """Structured logger — never raises into the request path."""

    policy: CommunityLoggingPolicy = field(default_factory=default_logging_policy)
    sink: LogSink = field(default_factory=NullLogSink)
    clock_ms: Callable[[], int] = field(default_factory=SequenceClock)
    request_id_factory: Callable[[], str] = field(
        default_factory=SequenceRequestIdFactory
    )
    _seq: int = 0
    _emitting: bool = False

    def __post_init__(self) -> None:
        self.policy = assert_supported_logging_policy(self.policy)

    @classmethod
    def create(
        cls,
        *,
        policy: CommunityLoggingPolicy | None = None,
        sink: LogSink | None = None,
        clock_ms: Callable[[], int] | None = None,
        request_id_factory: Callable[[], str] | None = None,
    ) -> CommunityCloudLogger:
        return cls(
            policy=policy or default_logging_policy(),
            sink=sink or NullLogSink(),
            clock_ms=clock_ms or SequenceClock(),
            request_id_factory=request_id_factory or SequenceRequestIdFactory(),
        )

    def emit(
        self,
        event_type: LogEventType,
        *,
        context: LoggingContext,
        status_code: int | None = None,
        duration_ms: int | None = None,
        error_code: str | None = None,
        level: LogLevel | None = None,
        timestamp: str | None = None,
        safe_event_fields: dict[str, object] | None = None,
    ) -> None:
        try:
            if self._emitting:
                return
            if event_type.value not in self.policy.allowed_event_types:
                return
            self._emitting = True
            self._seq += 1
            ts = timestamp
            if ts is None and self.policy.include_timestamps:
                # Only when policy enables timestamps; still clock-injected.
                ts = f"t+{int(self.clock_ms())}ms"
            safe_fields = assert_safe_event_log_fields(safe_event_fields or {})
            # Rate-limit and auth events must never include raw client host.
            client_host = context.client_host
            if event_type in {
                LogEventType.RATE_LIMIT_ALLOWED,
                LogEventType.RATE_LIMIT_EXCEEDED,
                LogEventType.RATE_LIMIT_UNAVAILABLE,
                LogEventType.AUTHENTICATION_SUCCEEDED,
                LogEventType.AUTHENTICATION_FAILED,
                LogEventType.AUTHENTICATION_UNAVAILABLE,
                LogEventType.AUTHORIZATION_DENIED,
            }:
                client_host = None
            event = StructuredLogEvent(
                event_type=event_type,
                level=level or level_for_event(event_type),
                api_version=context.api_version,
                method=context.method,
                route=context.route,
                request_id=context.request_id,
                policy_version=self.policy.policy_version,
                status_code=status_code,
                duration_ms=duration_ms,
                error_code=sanitize_error_code(
                    error_code, max_length=self.policy.max_field_length
                ),
                route_name=context.route_name,
                client_host=client_host,
                event_seq=self._seq,
                timestamp=ts,
                safe_event_reference=(
                    str(safe_fields["safe_event_reference"])
                    if "safe_event_reference" in safe_fields
                    else None
                ),
                retry_status=(
                    str(safe_fields["retry_status"])
                    if "retry_status" in safe_fields
                    else None
                ),
                source_event_type=(
                    str(safe_fields["source_event_type"])
                    if "source_event_type" in safe_fields
                    else None
                ),
                identity_policy_version=(
                    str(safe_fields["identity_policy_version"])
                    if "identity_policy_version" in safe_fields
                    else None
                ),
                telemetry_schema_version=(
                    str(safe_fields["telemetry_schema_version"])
                    if "telemetry_schema_version" in safe_fields
                    else None
                ),
                telemetry_policy_version=(
                    str(safe_fields["telemetry_policy_version"])
                    if "telemetry_policy_version" in safe_fields
                    else None
                ),
                metadata_schema_version=(
                    str(safe_fields["metadata_schema_version"])
                    if "metadata_schema_version" in safe_fields
                    else None
                ),
                metadata_policy_version=(
                    str(safe_fields["metadata_policy_version"])
                    if "metadata_policy_version" in safe_fields
                    else None
                ),
                client_type=(
                    str(safe_fields["client_type"])
                    if "client_type" in safe_fields
                    else None
                ),
                assessment_status=(
                    str(safe_fields["assessment_status"])
                    if "assessment_status" in safe_fields
                    else None
                ),
                cli_schema_version=(
                    str(safe_fields["cli_schema_version"])
                    if "cli_schema_version" in safe_fields
                    else None
                ),
                cli_policy_version=(
                    str(safe_fields["cli_policy_version"])
                    if "cli_policy_version" in safe_fields
                    else None
                ),
                canonical_operation=(
                    str(safe_fields["canonical_operation"])
                    if "canonical_operation" in safe_fields
                    else None
                ),
                lifecycle=(
                    str(safe_fields["lifecycle"]) if "lifecycle" in safe_fields else None
                ),
                result=(str(safe_fields["result"]) if "result" in safe_fields else None),
                extension_schema_version=(
                    str(safe_fields["extension_schema_version"])
                    if "extension_schema_version" in safe_fields
                    else None
                ),
                extension_policy_version=(
                    str(safe_fields["extension_policy_version"])
                    if "extension_policy_version" in safe_fields
                    else None
                ),
                ai_schema_version=(
                    str(safe_fields["ai_schema_version"])
                    if "ai_schema_version" in safe_fields
                    else None
                ),
                ai_policy_version=(
                    str(safe_fields["ai_policy_version"])
                    if "ai_policy_version" in safe_fields
                    else None
                ),
                canonical_capability=(
                    str(safe_fields["canonical_capability"])
                    if "canonical_capability" in safe_fields
                    else None
                ),
                outcome=(
                    str(safe_fields["outcome"]) if "outcome" in safe_fields else None
                ),
                rate_limit_policy_id=(
                    str(safe_fields["rate_limit_policy_id"])
                    if "rate_limit_policy_id" in safe_fields
                    else None
                ),
                rate_limit_limit=(
                    int(safe_fields["rate_limit_limit"])  # type: ignore[arg-type]
                    if "rate_limit_limit" in safe_fields
                    else None
                ),
                rate_limit_remaining=(
                    int(safe_fields["rate_limit_remaining"])  # type: ignore[arg-type]
                    if "rate_limit_remaining" in safe_fields
                    else None
                ),
                retry_after_seconds=(
                    int(safe_fields["retry_after_seconds"])  # type: ignore[arg-type]
                    if "retry_after_seconds" in safe_fields
                    else None
                ),
                safe_scope_reference=(
                    str(safe_fields["safe_scope_reference"])
                    if "safe_scope_reference" in safe_fields
                    else None
                ),
                authentication_policy_id=(
                    str(safe_fields["authentication_policy_id"])
                    if "authentication_policy_id" in safe_fields
                    else None
                ),
                authentication_reason=(
                    str(safe_fields["authentication_reason"])
                    if "authentication_reason" in safe_fields
                    else None
                ),
                verifier_status=(
                    str(safe_fields["verifier_status"])
                    if "verifier_status" in safe_fields
                    else None
                ),
                safe_client_reference=(
                    str(safe_fields["safe_client_reference"])
                    if "safe_client_reference" in safe_fields
                    else None
                ),
            )
            line = format_log_event(event)
            self.sink.write(line)
        except Exception:  # noqa: BLE001 - logging must never fail requests
            return
        finally:
            self._emitting = False

    def request_received(self, context: LoggingContext) -> None:
        self.emit(LogEventType.REQUEST_RECEIVED, context=context)

    def request_completed(
        self,
        context: LoggingContext,
        *,
        status_code: int,
        duration_ms: int,
    ) -> None:
        self.emit(
            LogEventType.REQUEST_COMPLETED,
            context=context,
            status_code=status_code,
            duration_ms=duration_ms,
        )

    def request_failed(
        self,
        context: LoggingContext,
        *,
        status_code: int,
        duration_ms: int,
        error_code: str | None = None,
    ) -> None:
        self.emit(
            LogEventType.REQUEST_FAILED,
            context=context,
            status_code=status_code,
            duration_ms=duration_ms,
            error_code=error_code,
            level=LogLevel.WARNING if status_code < 500 else LogLevel.ERROR,
        )

    def validation_failed(
        self,
        context: LoggingContext,
        *,
        status_code: int,
        error_code: str,
    ) -> None:
        self.emit(
            LogEventType.VALIDATION_FAILED,
            context=context,
            status_code=status_code,
            error_code=error_code,
        )

    def payload_rejected(
        self,
        context: LoggingContext,
        *,
        status_code: int,
        error_code: str,
    ) -> None:
        self.emit(
            LogEventType.PAYLOAD_REJECTED,
            context=context,
            status_code=status_code,
            error_code=error_code,
        )

    def health_checked(self, context: LoggingContext, *, status_code: int) -> None:
        self.emit(
            LogEventType.HEALTH_CHECKED,
            context=context,
            status_code=status_code,
        )

    def rate_limit_allowed(
        self,
        context: LoggingContext,
        *,
        status_code: int | None,
        decision: object,
        safe_log_policy: object,
    ) -> None:
        self.emit(
            LogEventType.RATE_LIMIT_ALLOWED,
            context=context,
            status_code=status_code,
            safe_event_fields=_rate_limit_safe_fields(decision, safe_log_policy),
        )

    def rate_limit_exceeded(
        self,
        context: LoggingContext,
        *,
        status_code: int,
        decision: object,
        safe_log_policy: object,
    ) -> None:
        from codestrata_platform.community_cloud_api.errors import ERROR_RATE_LIMIT_EXCEEDED

        self.emit(
            LogEventType.RATE_LIMIT_EXCEEDED,
            context=context,
            status_code=status_code,
            error_code=ERROR_RATE_LIMIT_EXCEEDED,
            safe_event_fields=_rate_limit_safe_fields(decision, safe_log_policy),
        )

    def rate_limit_unavailable(
        self,
        context: LoggingContext,
        *,
        status_code: int,
        decision: object,
        safe_log_policy: object,
    ) -> None:
        from codestrata_platform.community_cloud_api.errors import (
            ERROR_RATE_LIMIT_UNAVAILABLE,
        )

        self.emit(
            LogEventType.RATE_LIMIT_UNAVAILABLE,
            context=context,
            status_code=status_code,
            error_code=ERROR_RATE_LIMIT_UNAVAILABLE,
            safe_event_fields=_rate_limit_safe_fields(decision, safe_log_policy),
        )

    def authentication_succeeded(
        self,
        context: LoggingContext,
        *,
        status_code: int | None,
        decision: object,
        policy: object,
    ) -> None:
        _ = policy
        self.emit(
            LogEventType.AUTHENTICATION_SUCCEEDED,
            context=context,
            status_code=status_code,
            safe_event_fields=_auth_safe_fields(decision, success=True),
        )

    def authentication_failed(
        self,
        context: LoggingContext,
        *,
        status_code: int,
        decision: object,
        policy: object,
    ) -> None:
        from codestrata_platform.community_cloud_api.authentication.responses import (
            decision_error_code,
        )

        _ = policy
        self.emit(
            LogEventType.AUTHENTICATION_FAILED,
            context=context,
            status_code=status_code,
            error_code=decision_error_code(decision),  # type: ignore[arg-type]
            safe_event_fields=_auth_safe_fields(decision, success=False),
        )

    def authentication_unavailable(
        self,
        context: LoggingContext,
        *,
        status_code: int,
        decision: object,
        policy: object,
    ) -> None:
        from codestrata_platform.community_cloud_api.errors import (
            ERROR_AUTHENTICATION_UNAVAILABLE,
        )

        _ = policy
        self.emit(
            LogEventType.AUTHENTICATION_UNAVAILABLE,
            context=context,
            status_code=status_code,
            error_code=ERROR_AUTHENTICATION_UNAVAILABLE,
            safe_event_fields=_auth_safe_fields(decision, success=False),
        )

    def authorization_denied(
        self,
        context: LoggingContext,
        *,
        status_code: int,
        decision: object,
        policy: object,
    ) -> None:
        from codestrata_platform.community_cloud_api.errors import (
            ERROR_CLIENT_NOT_AUTHORIZED,
        )

        _ = policy
        self.emit(
            LogEventType.AUTHORIZATION_DENIED,
            context=context,
            status_code=status_code,
            error_code=ERROR_CLIENT_NOT_AUTHORIZED,
            safe_event_fields=_auth_safe_fields(decision, success=False),
        )


def _rate_limit_safe_fields(decision: object, safe_log_policy: object) -> dict[str, object]:
    fields: dict[str, object] = {}
    include_ref = getattr(safe_log_policy, "include_safe_scope_reference", True)
    include_limits = getattr(safe_log_policy, "include_limit_fields", True)
    policy_id = getattr(decision, "policy_id", None)
    if policy_id:
        fields["rate_limit_policy_id"] = str(policy_id)
    if include_limits:
        if getattr(decision, "limit", None) is not None:
            fields["rate_limit_limit"] = int(decision.limit)  # type: ignore[arg-type]
        if getattr(decision, "remaining", None) is not None:
            fields["rate_limit_remaining"] = int(decision.remaining)  # type: ignore[arg-type]
        retry = getattr(decision, "retry_after_seconds", None)
        if retry is not None:
            fields["retry_after_seconds"] = int(retry)
    if include_ref:
        ref = getattr(decision, "safe_scope_reference", None)
        if ref:
            fields["safe_scope_reference"] = str(ref)
    return fields


def _auth_safe_fields(decision: object, *, success: bool) -> dict[str, object]:
    fields: dict[str, object] = {}
    policy_id = getattr(decision, "policy_id", None)
    if policy_id:
        fields["authentication_policy_id"] = str(policy_id)
    reason = getattr(decision, "reason", None)
    if reason:
        fields["authentication_reason"] = str(reason)
    verifier = getattr(decision, "verifier_status", None)
    if verifier:
        fields["verifier_status"] = str(verifier)
    if success:
        ref = getattr(decision, "safe_client_reference", None)
        if ref:
            fields["safe_client_reference"] = str(ref)
        principal = getattr(decision, "principal", None)
        if principal is not None:
            client_type = getattr(principal, "client_type", None)
            if client_type:
                fields["client_type"] = str(client_type)
    return fields


def default_community_cloud_logger() -> CommunityCloudLogger:
    return CommunityCloudLogger.create()

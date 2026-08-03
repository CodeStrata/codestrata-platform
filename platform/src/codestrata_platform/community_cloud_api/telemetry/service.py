"""Telemetry ingestion application service (Slice 7.7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from starlette.responses import Response

from codestrata_platform.community_cloud_api.errors import (
    ERROR_EVENT_IDENTITY_CONFLICT,
    ERROR_EVENT_IDENTITY_RECORD_FAILED,
    ERROR_EVENT_IDENTITY_UNAVAILABLE,
    ERROR_INTERNAL,
    ERROR_TELEMETRY_REJECTED,
    ERROR_TELEMETRY_SINK_UNAVAILABLE,
)
from codestrata_platform.community_cloud_api.event_identity import (
    CommunityEventIdentityPolicy,
    EventIdentityLookup,
    EventIdentityRecorder,
    EventIdentityScope,
    RetryStatus,
    StoredEventIdentity,
    build_event_identity_conflict_error,
    classify_retry,
    default_event_identity_policy,
)
from codestrata_platform.community_cloud_api.logging.logger import CommunityCloudLogger
from codestrata_platform.community_cloud_api.logging.models import LogEventType
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.serialization import (
    build_error_response,
    build_json_response,
)
from codestrata_platform.community_cloud_api.telemetry.diagnostics import (
    TelemetryIngestionDiagnostics,
)
from codestrata_platform.community_cloud_api.telemetry.enums import (
    TelemetryIngestionStatus,
    TelemetrySinkStatus,
)
from codestrata_platform.community_cloud_api.telemetry.models import (
    TelemetryIngestionRequest,
)
from codestrata_platform.community_cloud_api.telemetry.policy import (
    CommunityTelemetryPolicy,
    default_telemetry_policy,
)
from codestrata_platform.community_cloud_api.telemetry.ports import (
    TelemetryEventSink,
    UnavailableTelemetryEventSink,
    ValidatedTelemetryEvent,
)
from codestrata_platform.community_cloud_api.telemetry.responses import (
    TelemetryIngestionResponse,
)


@dataclass
class IngestTelemetryEvent:
    """Orchestrate identity, sink acceptance, and deterministic acknowledgement."""

    sink: TelemetryEventSink = field(default_factory=UnavailableTelemetryEventSink)
    lookup: EventIdentityLookup | None = None
    recorder: EventIdentityRecorder | None = None
    telemetry_policy: CommunityTelemetryPolicy = field(
        default_factory=default_telemetry_policy
    )
    identity_policy: CommunityEventIdentityPolicy = field(
        default_factory=default_event_identity_policy
    )
    logger: CommunityCloudLogger | None = None
    last_diagnostics: TelemetryIngestionDiagnostics | None = None

    def handle(self, context: RequestContext) -> Response:
        request = context.validated_request
        if not isinstance(request, TelemetryIngestionRequest):
            return build_error_response(
                ERROR_INTERNAL,
                http_status=500,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        try:
            return self._ingest(context, request)
        except Exception:  # noqa: BLE001 - never leak backend details
            self._emit_safe(
                LogEventType.TELEMETRY_REJECTED,
                context,
                status_code=500,
                error_code=ERROR_INTERNAL,
            )
            return build_error_response(
                ERROR_INTERNAL,
                http_status=500,
                api_version=context.api_version,
                request_id=context.request_id,
            )

    def _ingest(
        self,
        context: RequestContext,
        request: TelemetryIngestionRequest,
    ) -> Response:
        self._emit_safe(
            LogEventType.TELEMETRY_RECEIVED,
            context,
            source_event_type=request.event_type,
            telemetry_schema_version=request.schema_version,
            telemetry_policy_version=self.telemetry_policy.policy_version,
        )

        limitations: list[str] = list(self.telemetry_policy.limitations)
        if request.installation_id is None:
            limitations.append("provisional_scope_without_installation_id")

        scope = EventIdentityScope(
            api_version=context.api_version,
            client_type=request.client.name,
            event_type=request.event_type,
            event_id=request.event_id,
            installation_id=request.installation_id,
        )

        # Fail closed when authoritative identity coordination is unavailable.
        if self.lookup is None or self.recorder is None:
            self.last_diagnostics = TelemetryIngestionDiagnostics(
                request_validated=True,
                identity_available=False,
                retry_status=RetryStatus.UNAVAILABLE.value,
                sink_status=None,
                identity_record_status=None,
                safe_event_reference=None,
                telemetry_schema_version=self.telemetry_policy.telemetry_schema_version,
                telemetry_policy_version=self.telemetry_policy.policy_version,
                limitations=tuple(sorted(set(limitations + ["no_authoritative_identity_store"]))),
            )
            self._emit_safe(
                LogEventType.TELEMETRY_REJECTED,
                context,
                status_code=503,
                error_code=ERROR_EVENT_IDENTITY_UNAVAILABLE,
                source_event_type=request.event_type,
                retry_status=RetryStatus.UNAVAILABLE.value,
                telemetry_schema_version=request.schema_version,
                telemetry_policy_version=self.telemetry_policy.policy_version,
            )
            return build_error_response(
                ERROR_EVENT_IDENTITY_UNAVAILABLE,
                http_status=503,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        decision = classify_retry(
            scope=scope,
            payload=request.fingerprint_payload(),
            lookup=self.lookup,
            policy=self.identity_policy,
        )

        if decision.status is RetryStatus.CONFLICTING_RETRY:
            self.last_diagnostics = TelemetryIngestionDiagnostics(
                request_validated=True,
                identity_available=True,
                retry_status=decision.status.value,
                sink_status=None,
                identity_record_status="skipped",
                safe_event_reference=decision.safe_event_reference,
                telemetry_schema_version=self.telemetry_policy.telemetry_schema_version,
                telemetry_policy_version=self.telemetry_policy.policy_version,
                limitations=tuple(sorted(set(limitations))),
            )
            self._emit_safe(
                LogEventType.TELEMETRY_CONFLICT,
                context,
                status_code=409,
                error_code=ERROR_EVENT_IDENTITY_CONFLICT,
                safe_event_reference=decision.safe_event_reference,
                source_event_type=request.event_type,
                retry_status=decision.status.value,
                identity_policy_version=self.identity_policy.policy_version,
                telemetry_schema_version=request.schema_version,
                telemetry_policy_version=self.telemetry_policy.policy_version,
            )
            envelope = build_event_identity_conflict_error(
                api_version=context.api_version,
                request_id=context.request_id,
                safe_event_reference=decision.safe_event_reference,
            )
            return build_json_response(
                envelope,
                status_code=409,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        if decision.status is RetryStatus.EXACT_RETRY:
            response = TelemetryIngestionResponse(
                status=TelemetryIngestionStatus.ALREADY_ACCEPTED,
                safe_event_reference=decision.safe_event_reference,
                retry_status=decision.status.value,
                schema_version=request.schema_version,
            )
            self.last_diagnostics = TelemetryIngestionDiagnostics(
                request_validated=True,
                identity_available=True,
                retry_status=decision.status.value,
                sink_status="skipped",
                identity_record_status="skipped",
                safe_event_reference=decision.safe_event_reference,
                telemetry_schema_version=self.telemetry_policy.telemetry_schema_version,
                telemetry_policy_version=self.telemetry_policy.policy_version,
                limitations=tuple(sorted(set(limitations))),
            )
            self._emit_safe(
                LogEventType.TELEMETRY_RETRY,
                context,
                status_code=200,
                safe_event_reference=decision.safe_event_reference,
                source_event_type=request.event_type,
                retry_status=decision.status.value,
                identity_policy_version=self.identity_policy.policy_version,
                telemetry_schema_version=request.schema_version,
                telemetry_policy_version=self.telemetry_policy.policy_version,
            )
            return build_json_response(
                response,
                status_code=200,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        if decision.status is not RetryStatus.FIRST_SEEN:
            # unavailable should not occur when lookup is configured, but fail closed.
            self.last_diagnostics = TelemetryIngestionDiagnostics(
                request_validated=True,
                identity_available=False,
                retry_status=decision.status.value,
                sink_status=None,
                identity_record_status=None,
                safe_event_reference=decision.safe_event_reference,
                telemetry_schema_version=self.telemetry_policy.telemetry_schema_version,
                telemetry_policy_version=self.telemetry_policy.policy_version,
                limitations=tuple(sorted(set(limitations))),
            )
            return build_error_response(
                ERROR_EVENT_IDENTITY_UNAVAILABLE,
                http_status=503,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        event = ValidatedTelemetryEvent(
            event_key=decision.event_key,
            safe_event_reference=decision.safe_event_reference,
            schema_version=request.schema_version,
            event_type=request.event_type,
            client=request.client,
            occurred_at=request.occurred_at,
            properties=request.properties,
            payload_fingerprint=decision.payload_fingerprint,
            identity_policy_version=self.identity_policy.policy_version,
            telemetry_policy_version=self.telemetry_policy.policy_version,
        )

        try:
            sink_result = self.sink.accept(event)
        except Exception:  # noqa: BLE001
            self.last_diagnostics = TelemetryIngestionDiagnostics(
                request_validated=True,
                identity_available=True,
                retry_status=decision.status.value,
                sink_status=TelemetrySinkStatus.UNAVAILABLE.value,
                identity_record_status="skipped",
                safe_event_reference=decision.safe_event_reference,
                telemetry_schema_version=self.telemetry_policy.telemetry_schema_version,
                telemetry_policy_version=self.telemetry_policy.policy_version,
                limitations=tuple(sorted(set(limitations))),
            )
            self._emit_safe(
                LogEventType.TELEMETRY_REJECTED,
                context,
                status_code=503,
                error_code=ERROR_TELEMETRY_SINK_UNAVAILABLE,
                safe_event_reference=decision.safe_event_reference,
                source_event_type=request.event_type,
                retry_status=decision.status.value,
                telemetry_schema_version=request.schema_version,
                telemetry_policy_version=self.telemetry_policy.policy_version,
            )
            return build_error_response(
                ERROR_TELEMETRY_SINK_UNAVAILABLE,
                http_status=503,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        if sink_result.status is TelemetrySinkStatus.UNAVAILABLE:
            self.last_diagnostics = TelemetryIngestionDiagnostics(
                request_validated=True,
                identity_available=True,
                retry_status=decision.status.value,
                sink_status=sink_result.status.value,
                identity_record_status="skipped",
                safe_event_reference=decision.safe_event_reference,
                telemetry_schema_version=self.telemetry_policy.telemetry_schema_version,
                telemetry_policy_version=self.telemetry_policy.policy_version,
                limitations=tuple(sorted(set(limitations))),
            )
            self._emit_safe(
                LogEventType.TELEMETRY_REJECTED,
                context,
                status_code=503,
                error_code=ERROR_TELEMETRY_SINK_UNAVAILABLE,
                safe_event_reference=decision.safe_event_reference,
                source_event_type=request.event_type,
                retry_status=decision.status.value,
                telemetry_schema_version=request.schema_version,
                telemetry_policy_version=self.telemetry_policy.policy_version,
            )
            return build_error_response(
                ERROR_TELEMETRY_SINK_UNAVAILABLE,
                http_status=503,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        if sink_result.status is TelemetrySinkStatus.REJECTED:
            self.last_diagnostics = TelemetryIngestionDiagnostics(
                request_validated=True,
                identity_available=True,
                retry_status=decision.status.value,
                sink_status=sink_result.status.value,
                identity_record_status="skipped",
                safe_event_reference=decision.safe_event_reference,
                telemetry_schema_version=self.telemetry_policy.telemetry_schema_version,
                telemetry_policy_version=self.telemetry_policy.policy_version,
                limitations=tuple(sorted(set(limitations))),
            )
            self._emit_safe(
                LogEventType.TELEMETRY_REJECTED,
                context,
                status_code=422,
                error_code=ERROR_TELEMETRY_REJECTED,
                safe_event_reference=decision.safe_event_reference,
                source_event_type=request.event_type,
                retry_status=decision.status.value,
                telemetry_schema_version=request.schema_version,
                telemetry_policy_version=self.telemetry_policy.policy_version,
            )
            return build_error_response(
                ERROR_TELEMETRY_REJECTED,
                http_status=422,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        # Record identity only after successful sink acceptance (best-effort).
        try:
            self.recorder.record(
                StoredEventIdentity(
                    event_key=decision.event_key,
                    payload_fingerprint=decision.payload_fingerprint,
                    event_type=scope.event_type,
                    client_type=scope.client_type,
                    identity_policy_version=self.identity_policy.policy_version,
                )
            )
            record_status = "recorded"
        except Exception:  # noqa: BLE001
            self.last_diagnostics = TelemetryIngestionDiagnostics(
                request_validated=True,
                identity_available=True,
                retry_status=decision.status.value,
                sink_status=sink_result.status.value,
                identity_record_status="failed",
                safe_event_reference=decision.safe_event_reference,
                telemetry_schema_version=self.telemetry_policy.telemetry_schema_version,
                telemetry_policy_version=self.telemetry_policy.policy_version,
                limitations=tuple(
                    sorted(
                        set(
                            limitations
                            + [
                                "sink_and_identity_record_not_atomic",
                                "identity_record_failed_after_sink_acceptance",
                            ]
                        )
                    )
                ),
            )
            self._emit_safe(
                LogEventType.TELEMETRY_REJECTED,
                context,
                status_code=503,
                error_code=ERROR_EVENT_IDENTITY_RECORD_FAILED,
                safe_event_reference=decision.safe_event_reference,
                source_event_type=request.event_type,
                retry_status=decision.status.value,
                identity_policy_version=self.identity_policy.policy_version,
                telemetry_schema_version=request.schema_version,
                telemetry_policy_version=self.telemetry_policy.policy_version,
            )
            return build_error_response(
                ERROR_EVENT_IDENTITY_RECORD_FAILED,
                http_status=503,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        response = TelemetryIngestionResponse(
            status=TelemetryIngestionStatus.ACCEPTED,
            safe_event_reference=decision.safe_event_reference,
            retry_status=decision.status.value,
            schema_version=request.schema_version,
        )
        self.last_diagnostics = TelemetryIngestionDiagnostics(
            request_validated=True,
            identity_available=True,
            retry_status=decision.status.value,
            sink_status=sink_result.status.value,
            identity_record_status=record_status,
            safe_event_reference=decision.safe_event_reference,
            telemetry_schema_version=self.telemetry_policy.telemetry_schema_version,
            telemetry_policy_version=self.telemetry_policy.policy_version,
            limitations=tuple(sorted(set(limitations))),
        )
        self._emit_safe(
            LogEventType.TELEMETRY_ACCEPTED,
            context,
            status_code=202,
            safe_event_reference=decision.safe_event_reference,
            source_event_type=request.event_type,
            retry_status=decision.status.value,
            identity_policy_version=self.identity_policy.policy_version,
            telemetry_schema_version=request.schema_version,
            telemetry_policy_version=self.telemetry_policy.policy_version,
        )
        return build_json_response(
            response,
            status_code=202,
            api_version=context.api_version,
            request_id=context.request_id,
        )

    def _emit_safe(
        self,
        event_type: LogEventType,
        context: RequestContext,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
        safe_event_reference: str | None = None,
        source_event_type: str | None = None,
        retry_status: str | None = None,
        identity_policy_version: str | None = None,
        telemetry_schema_version: str | None = None,
        telemetry_policy_version: str | None = None,
    ) -> None:
        if self.logger is None:
            return
        from codestrata_platform.community_cloud_api.logging.context import LoggingContext

        # Minimal logging context for telemetry-specific events.
        log_ctx = LoggingContext(
            api_version=context.api_version,
            method=context.method,
            route=context.path,
            request_id=context.request_id or "req-unknown",
            started_ms=0,
            route_name="telemetry.ingest",
        )
        fields: dict[str, object] = {}
        if safe_event_reference is not None:
            fields["safe_event_reference"] = safe_event_reference
        if source_event_type is not None:
            fields["source_event_type"] = source_event_type
        if retry_status is not None:
            fields["retry_status"] = retry_status
        if identity_policy_version is not None:
            fields["identity_policy_version"] = identity_policy_version
        if telemetry_schema_version is not None:
            fields["telemetry_schema_version"] = telemetry_schema_version
        if telemetry_policy_version is not None:
            fields["telemetry_policy_version"] = telemetry_policy_version
        self.logger.emit(
            event_type,
            context=log_ctx,
            status_code=status_code,
            error_code=error_code,
            safe_event_fields=fields or None,
        )


def build_fingerprint_material(request: TelemetryIngestionRequest) -> dict[str, Any]:
    return request.fingerprint_payload()

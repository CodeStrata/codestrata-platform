"""Assessment metadata ingestion application service (Slice 7.8)."""

from __future__ import annotations

from dataclasses import dataclass, field

from starlette.responses import Response

from codestrata_platform.community_cloud_api.assessment_metadata.diagnostics import (
    AssessmentMetadataDiagnostics,
)
from codestrata_platform.community_cloud_api.assessment_metadata.enums import (
    ASSESSMENT_METADATA_EVENT_TYPE,
    AssessmentMetadataIngestionStatus,
    AssessmentMetadataSinkStatus,
)
from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentMetadataRequest,
)
from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
    CommunityAssessmentMetadataPolicy,
    default_assessment_metadata_policy,
)
from codestrata_platform.community_cloud_api.assessment_metadata.ports import (
    AssessmentMetadataSink,
    UnavailableAssessmentMetadataSink,
    ValidatedAssessmentMetadataEvent,
)
from codestrata_platform.community_cloud_api.assessment_metadata.responses import (
    AssessmentMetadataResponse,
)
from codestrata_platform.community_cloud_api.errors import (
    ERROR_ASSESSMENT_METADATA_IDENTITY_UNAVAILABLE,
    ERROR_ASSESSMENT_METADATA_RECORD_FAILED,
    ERROR_ASSESSMENT_METADATA_REJECTED,
    ERROR_ASSESSMENT_METADATA_SINK_UNAVAILABLE,
    ERROR_EVENT_IDENTITY_CONFLICT,
    ERROR_INTERNAL,
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


@dataclass
class IngestAssessmentMetadata:
    """Orchestrate identity, sink acceptance, and deterministic acknowledgement."""

    sink: AssessmentMetadataSink = field(
        default_factory=UnavailableAssessmentMetadataSink
    )
    lookup: EventIdentityLookup | None = None
    recorder: EventIdentityRecorder | None = None
    metadata_policy: CommunityAssessmentMetadataPolicy = field(
        default_factory=default_assessment_metadata_policy
    )
    identity_policy: CommunityEventIdentityPolicy = field(
        default_factory=default_event_identity_policy
    )
    logger: CommunityCloudLogger | None = None
    last_diagnostics: AssessmentMetadataDiagnostics | None = None

    def handle(self, context: RequestContext) -> Response:
        request = context.validated_request
        if not isinstance(request, AssessmentMetadataRequest):
            return build_error_response(
                ERROR_INTERNAL,
                http_status=500,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        try:
            return self._ingest(context, request)
        except Exception:  # noqa: BLE001
            self._emit_safe(
                LogEventType.ASSESSMENT_METADATA_REJECTED,
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
        request: AssessmentMetadataRequest,
    ) -> Response:
        self._emit_safe(
            LogEventType.ASSESSMENT_METADATA_RECEIVED,
            context,
            source_event_type=ASSESSMENT_METADATA_EVENT_TYPE,
            metadata_schema_version=request.schema_version,
            metadata_policy_version=self.metadata_policy.policy_version,
            client_type=request.client.name,
            assessment_status=request.assessment.assessment_status,
        )

        limitations: list[str] = list(self.metadata_policy.limitations)
        if request.installation_id is None:
            limitations.append("provisional_scope_without_installation_id")

        scope = EventIdentityScope(
            api_version=context.api_version,
            client_type=request.client.name,
            event_type=ASSESSMENT_METADATA_EVENT_TYPE,
            event_id=request.event_id,
            installation_id=request.installation_id,
        )

        if self.lookup is None or self.recorder is None:
            self.last_diagnostics = AssessmentMetadataDiagnostics(
                request_validated=True,
                identity_available=False,
                retry_status=RetryStatus.UNAVAILABLE.value,
                sink_status=None,
                identity_record_status=None,
                safe_event_reference=None,
                metadata_schema_version=self.metadata_policy.schema_version,
                metadata_policy_version=self.metadata_policy.policy_version,
                limitations=tuple(
                    sorted(set(limitations + ["no_authoritative_identity_store"]))
                ),
            )
            self._emit_safe(
                LogEventType.ASSESSMENT_METADATA_REJECTED,
                context,
                status_code=503,
                error_code=ERROR_ASSESSMENT_METADATA_IDENTITY_UNAVAILABLE,
                source_event_type=ASSESSMENT_METADATA_EVENT_TYPE,
                retry_status=RetryStatus.UNAVAILABLE.value,
                metadata_schema_version=request.schema_version,
                metadata_policy_version=self.metadata_policy.policy_version,
                client_type=request.client.name,
                assessment_status=request.assessment.assessment_status,
            )
            return build_error_response(
                ERROR_ASSESSMENT_METADATA_IDENTITY_UNAVAILABLE,
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
            self.last_diagnostics = AssessmentMetadataDiagnostics(
                request_validated=True,
                identity_available=True,
                retry_status=decision.status.value,
                sink_status=None,
                identity_record_status="skipped",
                safe_event_reference=decision.safe_event_reference,
                metadata_schema_version=self.metadata_policy.schema_version,
                metadata_policy_version=self.metadata_policy.policy_version,
                limitations=tuple(sorted(set(limitations))),
            )
            self._emit_safe(
                LogEventType.ASSESSMENT_METADATA_CONFLICT,
                context,
                status_code=409,
                error_code=ERROR_EVENT_IDENTITY_CONFLICT,
                safe_event_reference=decision.safe_event_reference,
                source_event_type=ASSESSMENT_METADATA_EVENT_TYPE,
                retry_status=decision.status.value,
                identity_policy_version=self.identity_policy.policy_version,
                metadata_schema_version=request.schema_version,
                metadata_policy_version=self.metadata_policy.policy_version,
                client_type=request.client.name,
                assessment_status=request.assessment.assessment_status,
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
            response = AssessmentMetadataResponse(
                status=AssessmentMetadataIngestionStatus.ALREADY_ACCEPTED,
                safe_event_reference=decision.safe_event_reference,
                retry_status=decision.status.value,
                schema_version=request.schema_version,
            )
            self.last_diagnostics = AssessmentMetadataDiagnostics(
                request_validated=True,
                identity_available=True,
                retry_status=decision.status.value,
                sink_status="skipped",
                identity_record_status="skipped",
                safe_event_reference=decision.safe_event_reference,
                metadata_schema_version=self.metadata_policy.schema_version,
                metadata_policy_version=self.metadata_policy.policy_version,
                limitations=tuple(sorted(set(limitations))),
            )
            self._emit_safe(
                LogEventType.ASSESSMENT_METADATA_RETRY,
                context,
                status_code=200,
                safe_event_reference=decision.safe_event_reference,
                source_event_type=ASSESSMENT_METADATA_EVENT_TYPE,
                retry_status=decision.status.value,
                identity_policy_version=self.identity_policy.policy_version,
                metadata_schema_version=request.schema_version,
                metadata_policy_version=self.metadata_policy.policy_version,
                client_type=request.client.name,
                assessment_status=request.assessment.assessment_status,
            )
            return build_json_response(
                response,
                status_code=200,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        if decision.status is not RetryStatus.FIRST_SEEN:
            self.last_diagnostics = AssessmentMetadataDiagnostics(
                request_validated=True,
                identity_available=False,
                retry_status=decision.status.value,
                sink_status=None,
                identity_record_status=None,
                safe_event_reference=decision.safe_event_reference,
                metadata_schema_version=self.metadata_policy.schema_version,
                metadata_policy_version=self.metadata_policy.policy_version,
                limitations=tuple(sorted(set(limitations))),
            )
            return build_error_response(
                ERROR_ASSESSMENT_METADATA_IDENTITY_UNAVAILABLE,
                http_status=503,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        event = ValidatedAssessmentMetadataEvent(
            event_key=decision.event_key,
            safe_event_reference=decision.safe_event_reference,
            schema_version=request.schema_version,
            client=request.client,
            assessment=request.assessment,
            repository=request.repository,
            execution=request.execution,
            artifacts=request.artifacts,
            identity_policy_version=self.identity_policy.policy_version,
            metadata_policy_version=self.metadata_policy.policy_version,
            assessment_id=request.assessment_id,
            finding_aggregates=tuple(request.finding_aggregates),
            head_confidence=tuple(request.head_confidence),
        )

        try:
            sink_result = self.sink.accept(event, request=request)
        except Exception:  # noqa: BLE001
            return self._sink_unavailable(
                context, request, decision, limitations, decision.status.value
            )

        if sink_result.status is AssessmentMetadataSinkStatus.UNAVAILABLE:
            return self._sink_unavailable(
                context, request, decision, limitations, decision.status.value
            )

        if sink_result.status is AssessmentMetadataSinkStatus.REJECTED:
            self.last_diagnostics = AssessmentMetadataDiagnostics(
                request_validated=True,
                identity_available=True,
                retry_status=decision.status.value,
                sink_status=sink_result.status.value,
                identity_record_status="skipped",
                safe_event_reference=decision.safe_event_reference,
                metadata_schema_version=self.metadata_policy.schema_version,
                metadata_policy_version=self.metadata_policy.policy_version,
                limitations=tuple(sorted(set(limitations))),
            )
            self._emit_safe(
                LogEventType.ASSESSMENT_METADATA_REJECTED,
                context,
                status_code=422,
                error_code=ERROR_ASSESSMENT_METADATA_REJECTED,
                safe_event_reference=decision.safe_event_reference,
                source_event_type=ASSESSMENT_METADATA_EVENT_TYPE,
                retry_status=decision.status.value,
                metadata_schema_version=request.schema_version,
                metadata_policy_version=self.metadata_policy.policy_version,
                client_type=request.client.name,
                assessment_status=request.assessment.assessment_status,
            )
            return build_error_response(
                ERROR_ASSESSMENT_METADATA_REJECTED,
                http_status=422,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        try:
            assert self.recorder is not None
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
            self.last_diagnostics = AssessmentMetadataDiagnostics(
                request_validated=True,
                identity_available=True,
                retry_status=decision.status.value,
                sink_status=sink_result.status.value,
                identity_record_status="failed",
                safe_event_reference=decision.safe_event_reference,
                metadata_schema_version=self.metadata_policy.schema_version,
                metadata_policy_version=self.metadata_policy.policy_version,
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
                LogEventType.ASSESSMENT_METADATA_REJECTED,
                context,
                status_code=503,
                error_code=ERROR_ASSESSMENT_METADATA_RECORD_FAILED,
                safe_event_reference=decision.safe_event_reference,
                source_event_type=ASSESSMENT_METADATA_EVENT_TYPE,
                retry_status=decision.status.value,
                identity_policy_version=self.identity_policy.policy_version,
                metadata_schema_version=request.schema_version,
                metadata_policy_version=self.metadata_policy.policy_version,
                client_type=request.client.name,
                assessment_status=request.assessment.assessment_status,
            )
            return build_error_response(
                ERROR_ASSESSMENT_METADATA_RECORD_FAILED,
                http_status=503,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        response = AssessmentMetadataResponse(
            status=AssessmentMetadataIngestionStatus.ACCEPTED,
            safe_event_reference=decision.safe_event_reference,
            retry_status=decision.status.value,
            schema_version=request.schema_version,
        )
        self.last_diagnostics = AssessmentMetadataDiagnostics(
            request_validated=True,
            identity_available=True,
            retry_status=decision.status.value,
            sink_status=sink_result.status.value,
            identity_record_status=record_status,
            safe_event_reference=decision.safe_event_reference,
            metadata_schema_version=self.metadata_policy.schema_version,
            metadata_policy_version=self.metadata_policy.policy_version,
            limitations=tuple(sorted(set(limitations))),
        )
        self._emit_safe(
            LogEventType.ASSESSMENT_METADATA_ACCEPTED,
            context,
            status_code=202,
            safe_event_reference=decision.safe_event_reference,
            source_event_type=ASSESSMENT_METADATA_EVENT_TYPE,
            retry_status=decision.status.value,
            identity_policy_version=self.identity_policy.policy_version,
            metadata_schema_version=request.schema_version,
            metadata_policy_version=self.metadata_policy.policy_version,
            client_type=request.client.name,
            assessment_status=request.assessment.assessment_status,
        )
        return build_json_response(
            response,
            status_code=202,
            api_version=context.api_version,
            request_id=context.request_id,
        )

    def _sink_unavailable(
        self,
        context: RequestContext,
        request: AssessmentMetadataRequest,
        decision: object,
        limitations: list[str],
        retry_status: str,
    ) -> Response:
        safe_ref = getattr(decision, "safe_event_reference", None)
        self.last_diagnostics = AssessmentMetadataDiagnostics(
            request_validated=True,
            identity_available=True,
            retry_status=retry_status,
            sink_status=AssessmentMetadataSinkStatus.UNAVAILABLE.value,
            identity_record_status="skipped",
            safe_event_reference=safe_ref,
            metadata_schema_version=self.metadata_policy.schema_version,
            metadata_policy_version=self.metadata_policy.policy_version,
            limitations=tuple(sorted(set(limitations))),
        )
        self._emit_safe(
            LogEventType.ASSESSMENT_METADATA_REJECTED,
            context,
            status_code=503,
            error_code=ERROR_ASSESSMENT_METADATA_SINK_UNAVAILABLE,
            safe_event_reference=safe_ref,
            source_event_type=ASSESSMENT_METADATA_EVENT_TYPE,
            retry_status=retry_status,
            metadata_schema_version=request.schema_version,
            metadata_policy_version=self.metadata_policy.policy_version,
            client_type=request.client.name,
            assessment_status=request.assessment.assessment_status,
        )
        return build_error_response(
            ERROR_ASSESSMENT_METADATA_SINK_UNAVAILABLE,
            http_status=503,
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
        metadata_schema_version: str | None = None,
        metadata_policy_version: str | None = None,
        client_type: str | None = None,
        assessment_status: str | None = None,
    ) -> None:
        if self.logger is None:
            return
        from codestrata_platform.community_cloud_api.logging.context import LoggingContext

        log_ctx = LoggingContext(
            api_version=context.api_version,
            method=context.method,
            route=context.path,
            request_id=context.request_id or "req-unknown",
            started_ms=0,
            route_name="assessment_metadata.ingest",
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
        if metadata_schema_version is not None:
            fields["metadata_schema_version"] = metadata_schema_version
        if metadata_policy_version is not None:
            fields["metadata_policy_version"] = metadata_policy_version
        if client_type is not None:
            fields["client_type"] = client_type
        if assessment_status is not None:
            fields["assessment_status"] = assessment_status
        self.logger.emit(
            event_type,
            context=log_ctx,
            status_code=status_code,
            error_code=error_code,
            safe_event_fields=fields or None,
        )

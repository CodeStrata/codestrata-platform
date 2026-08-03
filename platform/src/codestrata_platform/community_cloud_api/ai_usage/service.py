"""AI usage ingestion application service (Slice 7.11)."""

from __future__ import annotations

from dataclasses import dataclass, field

from starlette.responses import Response

from codestrata_platform.community_cloud_api.ai_usage.diagnostics import AiUsageDiagnostics
from codestrata_platform.community_cloud_api.ai_usage.enums import (
    AI_USAGE_SOURCE_TYPE,
    AiUsageIngestionStatus,
    AiUsageSinkStatus,
)
from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest
from codestrata_platform.community_cloud_api.ai_usage.policy import (
    CommunityAiUsagePolicy,
    default_ai_usage_policy,
)
from codestrata_platform.community_cloud_api.ai_usage.ports import (
    AiUsageSink,
    UnavailableAiUsageSink,
    ValidatedAiUsageEvent,
)
from codestrata_platform.community_cloud_api.ai_usage.responses import AiUsageResponse
from codestrata_platform.community_cloud_api.errors import (
    ERROR_AI_USAGE_IDENTITY_UNAVAILABLE,
    ERROR_AI_USAGE_RECORD_FAILED,
    ERROR_AI_USAGE_REJECTED,
    ERROR_AI_USAGE_SINK_UNAVAILABLE,
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
class IngestAiUsage:
    """Orchestrate identity, sink acceptance, and deterministic acknowledgement."""

    sink: AiUsageSink = field(default_factory=UnavailableAiUsageSink)
    lookup: EventIdentityLookup | None = None
    recorder: EventIdentityRecorder | None = None
    ai_policy: CommunityAiUsagePolicy = field(default_factory=default_ai_usage_policy)
    identity_policy: CommunityEventIdentityPolicy = field(
        default_factory=default_event_identity_policy
    )
    logger: CommunityCloudLogger | None = None
    last_diagnostics: AiUsageDiagnostics | None = None

    def handle(self, context: RequestContext) -> Response:
        request = context.validated_request
        if not isinstance(request, AiUsageRequest):
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
                LogEventType.AI_USAGE_REJECTED,
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

    def _ingest(self, context: RequestContext, request: AiUsageRequest) -> Response:
        self._emit_safe(
            LogEventType.AI_USAGE_RECEIVED,
            context,
            source_event_type=AI_USAGE_SOURCE_TYPE,
            ai_schema_version=request.schema_version,
            ai_policy_version=self.ai_policy.policy_version,
            canonical_capability=request.usage.capability,
            outcome=request.usage.outcome,
        )

        limitations = list(self.ai_policy.limitations)
        if request.installation_id is None:
            limitations.append("provisional_scope_without_installation_id")

        scope = EventIdentityScope(
            api_version=context.api_version,
            client_type=request.client.name,
            event_type=AI_USAGE_SOURCE_TYPE,
            event_id=request.event_id,
            installation_id=request.installation_id,
        )

        if self.lookup is None or self.recorder is None:
            self.last_diagnostics = self._diag(
                False,
                RetryStatus.UNAVAILABLE.value,
                None,
                None,
                None,
                limitations + ["no_authoritative_identity_store"],
            )
            self._emit_safe(
                LogEventType.AI_USAGE_REJECTED,
                context,
                status_code=503,
                error_code=ERROR_AI_USAGE_IDENTITY_UNAVAILABLE,
                source_event_type=AI_USAGE_SOURCE_TYPE,
                retry_status=RetryStatus.UNAVAILABLE.value,
                ai_schema_version=request.schema_version,
                ai_policy_version=self.ai_policy.policy_version,
                canonical_capability=request.usage.capability,
                outcome=request.usage.outcome,
            )
            return build_error_response(
                ERROR_AI_USAGE_IDENTITY_UNAVAILABLE,
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
            self.last_diagnostics = self._diag(
                True,
                decision.status.value,
                None,
                "skipped",
                decision.safe_event_reference,
                limitations,
            )
            self._emit_safe(
                LogEventType.AI_USAGE_CONFLICT,
                context,
                status_code=409,
                error_code=ERROR_EVENT_IDENTITY_CONFLICT,
                safe_event_reference=decision.safe_event_reference,
                source_event_type=AI_USAGE_SOURCE_TYPE,
                retry_status=decision.status.value,
                identity_policy_version=self.identity_policy.policy_version,
                ai_schema_version=request.schema_version,
                ai_policy_version=self.ai_policy.policy_version,
                canonical_capability=request.usage.capability,
                outcome=request.usage.outcome,
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
            response = AiUsageResponse(
                status=AiUsageIngestionStatus.ALREADY_ACCEPTED,
                safe_event_reference=decision.safe_event_reference,
                retry_status=decision.status.value,
                schema_version=request.schema_version,
            )
            self.last_diagnostics = self._diag(
                True,
                decision.status.value,
                "skipped",
                "skipped",
                decision.safe_event_reference,
                limitations,
            )
            self._emit_safe(
                LogEventType.AI_USAGE_RETRY,
                context,
                status_code=200,
                safe_event_reference=decision.safe_event_reference,
                source_event_type=AI_USAGE_SOURCE_TYPE,
                retry_status=decision.status.value,
                identity_policy_version=self.identity_policy.policy_version,
                ai_schema_version=request.schema_version,
                ai_policy_version=self.ai_policy.policy_version,
                canonical_capability=request.usage.capability,
                outcome=request.usage.outcome,
            )
            return build_json_response(
                response,
                status_code=200,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        if decision.status is not RetryStatus.FIRST_SEEN:
            return build_error_response(
                ERROR_AI_USAGE_IDENTITY_UNAVAILABLE,
                http_status=503,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        event = ValidatedAiUsageEvent(
            event_key=decision.event_key,
            safe_event_reference=decision.safe_event_reference,
            schema_version=request.schema_version,
            client=request.client,
            usage=request.usage,
            context=request.context,
            identity_policy_version=self.identity_policy.policy_version,
            ai_usage_policy_version=self.ai_policy.policy_version,
            capability_catalog_version=self.ai_policy.capability_catalog_version,
            provider_catalog_version=self.ai_policy.provider_catalog_version,
            model_catalog_version=self.ai_policy.model_catalog_version,
        )

        try:
            sink_result = self.sink.accept(event)
        except Exception:  # noqa: BLE001
            return self._sink_unavailable(context, request, decision, limitations)

        if sink_result.status is AiUsageSinkStatus.UNAVAILABLE:
            return self._sink_unavailable(context, request, decision, limitations)

        if sink_result.status is AiUsageSinkStatus.REJECTED:
            self.last_diagnostics = self._diag(
                True,
                decision.status.value,
                sink_result.status.value,
                "skipped",
                decision.safe_event_reference,
                limitations,
            )
            self._emit_safe(
                LogEventType.AI_USAGE_REJECTED,
                context,
                status_code=422,
                error_code=ERROR_AI_USAGE_REJECTED,
                safe_event_reference=decision.safe_event_reference,
                source_event_type=AI_USAGE_SOURCE_TYPE,
                retry_status=decision.status.value,
                ai_schema_version=request.schema_version,
                ai_policy_version=self.ai_policy.policy_version,
                canonical_capability=request.usage.capability,
                outcome=request.usage.outcome,
            )
            return build_error_response(
                ERROR_AI_USAGE_REJECTED,
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
            self.last_diagnostics = self._diag(
                True,
                decision.status.value,
                sink_result.status.value,
                "failed",
                decision.safe_event_reference,
                limitations
                + [
                    "sink_and_identity_record_not_atomic",
                    "identity_record_failed_after_sink_acceptance",
                ],
            )
            self._emit_safe(
                LogEventType.AI_USAGE_REJECTED,
                context,
                status_code=503,
                error_code=ERROR_AI_USAGE_RECORD_FAILED,
                safe_event_reference=decision.safe_event_reference,
                source_event_type=AI_USAGE_SOURCE_TYPE,
                retry_status=decision.status.value,
                identity_policy_version=self.identity_policy.policy_version,
                ai_schema_version=request.schema_version,
                ai_policy_version=self.ai_policy.policy_version,
                canonical_capability=request.usage.capability,
                outcome=request.usage.outcome,
            )
            return build_error_response(
                ERROR_AI_USAGE_RECORD_FAILED,
                http_status=503,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        response = AiUsageResponse(
            status=AiUsageIngestionStatus.ACCEPTED,
            safe_event_reference=decision.safe_event_reference,
            retry_status=decision.status.value,
            schema_version=request.schema_version,
        )
        self.last_diagnostics = self._diag(
            True,
            decision.status.value,
            sink_result.status.value,
            record_status,
            decision.safe_event_reference,
            limitations,
        )
        self._emit_safe(
            LogEventType.AI_USAGE_ACCEPTED,
            context,
            status_code=202,
            safe_event_reference=decision.safe_event_reference,
            source_event_type=AI_USAGE_SOURCE_TYPE,
            retry_status=decision.status.value,
            identity_policy_version=self.identity_policy.policy_version,
            ai_schema_version=request.schema_version,
            ai_policy_version=self.ai_policy.policy_version,
            canonical_capability=request.usage.capability,
            outcome=request.usage.outcome,
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
        request: AiUsageRequest,
        decision: object,
        limitations: list[str],
    ) -> Response:
        safe_ref = getattr(decision, "safe_event_reference", None)
        retry_status = getattr(getattr(decision, "status", None), "value", None) or getattr(
            decision, "status", None
        )
        self.last_diagnostics = self._diag(
            True,
            str(retry_status) if retry_status else None,
            AiUsageSinkStatus.UNAVAILABLE.value,
            "skipped",
            safe_ref,
            limitations,
        )
        self._emit_safe(
            LogEventType.AI_USAGE_REJECTED,
            context,
            status_code=503,
            error_code=ERROR_AI_USAGE_SINK_UNAVAILABLE,
            safe_event_reference=safe_ref,
            source_event_type=AI_USAGE_SOURCE_TYPE,
            retry_status=str(retry_status) if retry_status else None,
            ai_schema_version=request.schema_version,
            ai_policy_version=self.ai_policy.policy_version,
            canonical_capability=request.usage.capability,
            outcome=request.usage.outcome,
        )
        return build_error_response(
            ERROR_AI_USAGE_SINK_UNAVAILABLE,
            http_status=503,
            api_version=context.api_version,
            request_id=context.request_id,
        )

    def _diag(
        self,
        identity_available: bool,
        retry_status: str | None,
        sink_status: str | None,
        identity_record_status: str | None,
        safe_ref: str | None,
        limitations: list[str],
    ) -> AiUsageDiagnostics:
        return AiUsageDiagnostics(
            request_validated=True,
            identity_available=identity_available,
            retry_status=retry_status,
            sink_status=sink_status,
            identity_record_status=identity_record_status,
            safe_event_reference=safe_ref,
            schema_version=self.ai_policy.schema_version,
            policy_version=self.ai_policy.policy_version,
            capability_catalog_version=self.ai_policy.capability_catalog_version,
            provider_catalog_version=self.ai_policy.provider_catalog_version,
            model_catalog_version=self.ai_policy.model_catalog_version,
            limitations=tuple(sorted(set(limitations))),
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
        ai_schema_version: str | None = None,
        ai_policy_version: str | None = None,
        canonical_capability: str | None = None,
        outcome: str | None = None,
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
            route_name="ai_usage.ingest",
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
        if ai_schema_version is not None:
            fields["ai_schema_version"] = ai_schema_version
        if ai_policy_version is not None:
            fields["ai_policy_version"] = ai_policy_version
        if canonical_capability is not None:
            fields["canonical_capability"] = canonical_capability
        if outcome is not None:
            fields["outcome"] = outcome
        self.logger.emit(
            event_type,
            context=log_ctx,
            status_code=status_code,
            error_code=error_code,
            safe_event_fields=fields or None,
        )

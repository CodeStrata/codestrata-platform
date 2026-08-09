"""Data-lake-backed event sinks for Community Cloud ingestion (Slice 17.7).

Compose envelope build → stream projection → immutable store write.
Quarantine uses allowlisted reason codes only — never secrets or stack traces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.ai_usage.enums import AiUsageSinkStatus
from codestrata_platform.community_cloud_api.ai_usage.ports import (
    AiUsageSinkResult,
    ValidatedAiUsageEvent,
)
from codestrata_platform.community_cloud_api.assessment_metadata.enums import (
    AssessmentMetadataSinkStatus,
)
from codestrata_platform.community_cloud_api.assessment_metadata.ports import (
    AssessmentMetadataSinkResult,
    ValidatedAssessmentMetadataEvent,
)
from codestrata_platform.community_cloud_api.cli_events.enums import CliEventSinkStatus
from codestrata_platform.community_cloud_api.cli_events.ports import (
    CliEventSinkResult,
    ValidatedCliEvent,
)
from codestrata_platform.community_cloud_api.data_lake.accepted_clock import (
    AcceptanceClock,
    SystemAcceptanceClock,
)
from codestrata_platform.community_cloud_api.data_lake.enums import (
    EventStream,
    QuarantineReasonCode,
    QuarantineValidationStage,
    StorageWriteStatus,
)
from codestrata_platform.community_cloud_api.data_lake.envelope_builders import (
    build_data_lake_envelope,
)
from codestrata_platform.community_cloud_api.data_lake.envelope_models import EnvelopeErrorCode
from codestrata_platform.community_cloud_api.data_lake.envelope_validation import EnvelopeBuildError
from codestrata_platform.community_cloud_api.data_lake.ports import CommunityDataLakeStore
from codestrata_platform.community_cloud_api.data_lake.quarantine_error_mapping import (
    QuarantineErrorMapping,
    map_exception_to_quarantine,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_models import (
    build_quarantine_record,
)
from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    PartitionProjectionError as AiUsagePartitionProjectionError,
)
from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    project_ai_usage_storage_object,
    store_projected_ai_usage,
)
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    PartitionProjectionError as AssessmentMetadataPartitionProjectionError,
)
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    project_assessment_metadata_storage_object,
    store_projected_assessment_metadata,
)
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    PartitionProjectionError as CliEventPartitionProjectionError,
)
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    project_cli_event_storage_object,
    store_projected_cli_event,
)
from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    PartitionProjectionError as ExtensionEventPartitionProjectionError,
)
from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    project_extension_event_storage_object,
    store_projected_extension_event,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    PartitionProjectionError as TelemetryPartitionProjectionError,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    project_telemetry_storage_object,
    store_projected_telemetry,
)
from codestrata_platform.community_cloud_api.extension_events.enums import (
    ExtensionEventSinkStatus,
)
from codestrata_platform.community_cloud_api.extension_events.ports import (
    ExtensionEventSinkResult,
    ValidatedExtensionEvent,
)
from codestrata_platform.community_cloud_api.telemetry.enums import TelemetrySinkStatus
from codestrata_platform.community_cloud_api.telemetry.ports import (
    TelemetrySinkResult,
    ValidatedTelemetryEvent,
)

_ENVELOPE_ERROR_TO_REASON: dict[str, str] = {
    EnvelopeErrorCode.INVALID_ENVELOPE.value: QuarantineReasonCode.INVALID_ENVELOPE.value,
    EnvelopeErrorCode.UNSUPPORTED_ENVELOPE_SCHEMA.value: (
        QuarantineReasonCode.UNSUPPORTED_ENVELOPE_SCHEMA.value
    ),
    EnvelopeErrorCode.UNSUPPORTED_SOURCE_SCHEMA.value: (
        QuarantineReasonCode.UNSUPPORTED_SOURCE_SCHEMA.value
    ),
    EnvelopeErrorCode.UNSUPPORTED_SOURCE_POLICY.value: (
        QuarantineReasonCode.UNSUPPORTED_SOURCE_POLICY.value
    ),
    EnvelopeErrorCode.STREAM_CONTRACT_MISMATCH.value: (
        QuarantineReasonCode.STREAM_CONTRACT_MISMATCH.value
    ),
    EnvelopeErrorCode.INVALID_SOURCE_PAYLOAD.value: (
        QuarantineReasonCode.INVALID_SOURCE_PAYLOAD.value
    ),
    EnvelopeErrorCode.UNSAFE_ENVELOPE.value: QuarantineReasonCode.UNSAFE_PAYLOAD.value,
    EnvelopeErrorCode.ENVELOPE_TOO_LARGE.value: QuarantineReasonCode.ENVELOPE_TOO_LARGE.value,
    EnvelopeErrorCode.ENVELOPE_SERIALIZATION_FAILED.value: (
        QuarantineReasonCode.SERIALIZATION_FAILURE.value
    ),
    EnvelopeErrorCode.ENVELOPE_DESERIALIZATION_FAILED.value: (
        QuarantineReasonCode.SERIALIZATION_FAILURE.value
    ),
}


def _map_storage_write_to_sink(
    status: StorageWriteStatus,
    *,
    accepted_reason: str,
    rejected_reason: str,
    unavailable_reason: str,
) -> tuple[str, str]:
    """Return ``(sink_status_value, reason)`` for a storage write outcome."""

    if status in (StorageWriteStatus.STORED, StorageWriteStatus.ALREADY_EXISTS):
        return "accepted", accepted_reason
    if status in (StorageWriteStatus.CONFLICT, StorageWriteStatus.REJECTED):
        return "rejected", rejected_reason
    return "unavailable", unavailable_reason


def _quarantine_mapping_for_exception(exc: BaseException) -> QuarantineErrorMapping | None:
    mapping = map_exception_to_quarantine(exc)
    if mapping is not None:
        return mapping
    if isinstance(exc, EnvelopeBuildError):
        code = exc.code.value if isinstance(exc.code, EnvelopeErrorCode) else str(exc.code)
        reason = _ENVELOPE_ERROR_TO_REASON.get(
            code, QuarantineReasonCode.INVALID_ENVELOPE.value
        )
        return QuarantineErrorMapping(
            quarantine_reason=reason,
            validation_stage=QuarantineValidationStage.ENVELOPE_VALIDATION.value,
            diagnostic_codes=(code if code in _ENVELOPE_ERROR_TO_REASON else "invalid_envelope",),
        )
    # PartitionProjectionError variants expose allowlisted ``code`` attributes.
    code_attr = getattr(exc, "code", None)
    if isinstance(code_attr, str) and code_attr:
        return QuarantineErrorMapping(
            quarantine_reason=QuarantineReasonCode.INVALID_PARTITION.value,
            validation_stage=QuarantineValidationStage.PARTITION_PROJECTION.value,
            diagnostic_codes=(code_attr[:64],),
        )
    return None


def _maybe_quarantine(
    store: CommunityDataLakeStore,
    *,
    exc: BaseException,
    event_stream: EventStream,
    safe_event_reference: str,
    clock: AcceptanceClock,
) -> None:
    mapping = _quarantine_mapping_for_exception(exc)
    if mapping is None or not mapping.should_quarantine:
        return
    record = build_quarantine_record(
        quarantine_reason=mapping.quarantine_reason,
        validation_stage=mapping.validation_stage,
        clock=clock,
        event_stream=event_stream.value,
        safe_event_reference=safe_event_reference,
        diagnostic_codes=mapping.diagnostic_codes,
    )
    try:
        store.quarantine_event(record)
    except Exception:  # noqa: BLE001 — quarantine best-effort; never leak detail
        return


@dataclass(frozen=True, slots=True)
class _SinkOutcome:
    status: str
    reason: str


def _accept_stream(
    *,
    store: CommunityDataLakeStore,
    clock: AcceptanceClock,
    event_stream: EventStream,
    request: Any | None,
    event_key: str,
    safe_event_reference: str,
    project,
    store_projected,
    accepted_reason: str,
    rejected_reason: str,
    unavailable_reason: str,
    missing_request_reason: str,
) -> _SinkOutcome:
    if request is None:
        return _SinkOutcome(status="unavailable", reason=missing_request_reason)

    try:
        envelope = build_data_lake_envelope(
            event_stream=event_stream,
            request=request,
            event_key=event_key,
            safe_event_reference=safe_event_reference,
            clock=clock,
        )
        projection = project(envelope)
        write = store_projected(store, projection)
    except (
        EnvelopeBuildError,
        TelemetryPartitionProjectionError,
        AssessmentMetadataPartitionProjectionError,
        CliEventPartitionProjectionError,
        ExtensionEventPartitionProjectionError,
        AiUsagePartitionProjectionError,
    ) as exc:
        _maybe_quarantine(
            store,
            exc=exc,
            event_stream=event_stream,
            safe_event_reference=safe_event_reference,
            clock=clock,
        )
        return _SinkOutcome(status="rejected", reason=rejected_reason)
    except Exception as exc:  # noqa: BLE001
        mapping = _quarantine_mapping_for_exception(exc)
        if mapping is not None and mapping.should_quarantine:
            _maybe_quarantine(
                store,
                exc=exc,
                event_stream=event_stream,
                safe_event_reference=safe_event_reference,
                clock=clock,
            )
            return _SinkOutcome(status="rejected", reason=rejected_reason)
        return _SinkOutcome(status="unavailable", reason=unavailable_reason)

    status, reason = _map_storage_write_to_sink(
        write.status,
        accepted_reason=accepted_reason,
        rejected_reason=rejected_reason,
        unavailable_reason=unavailable_reason,
    )
    return _SinkOutcome(status=status, reason=reason)


@dataclass(slots=True)
class DataLakeTelemetryEventSink:
    """Durable telemetry sink backed by Community Data Lake storage."""

    store: CommunityDataLakeStore
    clock: AcceptanceClock | None = None

    def accept(
        self,
        event: ValidatedTelemetryEvent,
        *,
        request: Any | None = None,
    ) -> TelemetrySinkResult:
        clock = self.clock or SystemAcceptanceClock()
        outcome = _accept_stream(
            store=self.store,
            clock=clock,
            event_stream=EventStream.TELEMETRY,
            request=request,
            event_key=event.event_key,
            safe_event_reference=event.safe_event_reference,
            project=project_telemetry_storage_object,
            store_projected=store_projected_telemetry,
            accepted_reason="accepted",
            rejected_reason="telemetry_rejected",
            unavailable_reason="telemetry_sink_unavailable",
            missing_request_reason="telemetry_sink_unavailable",
        )
        return TelemetrySinkResult(
            status=TelemetrySinkStatus(outcome.status),
            reason=outcome.reason,
        )


@dataclass(slots=True)
class DataLakeAssessmentMetadataSink:
    store: CommunityDataLakeStore
    clock: AcceptanceClock | None = None

    def accept(
        self,
        event: ValidatedAssessmentMetadataEvent,
        *,
        request: Any | None = None,
    ) -> AssessmentMetadataSinkResult:
        clock = self.clock or SystemAcceptanceClock()
        outcome = _accept_stream(
            store=self.store,
            clock=clock,
            event_stream=EventStream.ASSESSMENT_METADATA,
            request=request,
            event_key=event.event_key,
            safe_event_reference=event.safe_event_reference,
            project=project_assessment_metadata_storage_object,
            store_projected=store_projected_assessment_metadata,
            accepted_reason="accepted",
            rejected_reason="assessment_metadata_rejected",
            unavailable_reason="assessment_metadata_sink_unavailable",
            missing_request_reason="assessment_metadata_sink_unavailable",
        )
        return AssessmentMetadataSinkResult(
            status=AssessmentMetadataSinkStatus(outcome.status),
            reason=outcome.reason,
        )


@dataclass(slots=True)
class DataLakeCliEventSink:
    store: CommunityDataLakeStore
    clock: AcceptanceClock | None = None

    def accept(
        self,
        event: ValidatedCliEvent,
        *,
        request: Any | None = None,
    ) -> CliEventSinkResult:
        clock = self.clock or SystemAcceptanceClock()
        outcome = _accept_stream(
            store=self.store,
            clock=clock,
            event_stream=EventStream.CLI_EVENT,
            request=request,
            event_key=event.event_key,
            safe_event_reference=event.safe_event_reference,
            project=project_cli_event_storage_object,
            store_projected=store_projected_cli_event,
            accepted_reason="accepted",
            rejected_reason="cli_event_rejected",
            unavailable_reason="cli_event_sink_unavailable",
            missing_request_reason="cli_event_sink_unavailable",
        )
        return CliEventSinkResult(
            status=CliEventSinkStatus(outcome.status),
            reason=outcome.reason,
        )


@dataclass(slots=True)
class DataLakeExtensionEventSink:
    store: CommunityDataLakeStore
    clock: AcceptanceClock | None = None

    def accept(
        self,
        event: ValidatedExtensionEvent,
        *,
        request: Any | None = None,
    ) -> ExtensionEventSinkResult:
        clock = self.clock or SystemAcceptanceClock()
        outcome = _accept_stream(
            store=self.store,
            clock=clock,
            event_stream=EventStream.EXTENSION_EVENT,
            request=request,
            event_key=event.event_key,
            safe_event_reference=event.safe_event_reference,
            project=project_extension_event_storage_object,
            store_projected=store_projected_extension_event,
            accepted_reason="accepted",
            rejected_reason="extension_event_rejected",
            unavailable_reason="extension_event_sink_unavailable",
            missing_request_reason="extension_event_sink_unavailable",
        )
        return ExtensionEventSinkResult(
            status=ExtensionEventSinkStatus(outcome.status),
            reason=outcome.reason,
        )


@dataclass(slots=True)
class DataLakeAiUsageSink:
    store: CommunityDataLakeStore
    clock: AcceptanceClock | None = None

    def accept(
        self,
        event: ValidatedAiUsageEvent,
        *,
        request: Any | None = None,
    ) -> AiUsageSinkResult:
        clock = self.clock or SystemAcceptanceClock()
        outcome = _accept_stream(
            store=self.store,
            clock=clock,
            event_stream=EventStream.AI_USAGE,
            request=request,
            event_key=event.event_key,
            safe_event_reference=event.safe_event_reference,
            project=project_ai_usage_storage_object,
            store_projected=store_projected_ai_usage,
            accepted_reason="accepted",
            rejected_reason="ai_usage_rejected",
            unavailable_reason="ai_usage_sink_unavailable",
            missing_request_reason="ai_usage_sink_unavailable",
        )
        return AiUsageSinkResult(
            status=AiUsageSinkStatus(outcome.status),
            reason=outcome.reason,
        )


__all__ = [
    "DataLakeAiUsageSink",
    "DataLakeAssessmentMetadataSink",
    "DataLakeCliEventSink",
    "DataLakeExtensionEventSink",
    "DataLakeTelemetryEventSink",
]

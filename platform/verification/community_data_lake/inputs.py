"""Typed verification inputs for all accepted streams and quarantine (Slice 8.14)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest
from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentMetadataRequest,
)
from codestrata_platform.community_cloud_api.cli_events.models import CliEventRequest
from codestrata_platform.community_cloud_api.extension_events.models import ExtensionEventRequest
from codestrata_platform.community_cloud_api.data_lake.accepted_clock import FixedAcceptanceClock
from codestrata_platform.community_cloud_api.data_lake.envelope_builders import (
    build_data_lake_envelope,
)
from codestrata_platform.community_cloud_api.data_lake.objects import ImmutableRawStorageObject
from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
    ImmutableQuarantineStorageObject,
    build_quarantine_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    project_ai_usage_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    project_assessment_metadata_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    project_cli_event_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    project_extension_event_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    project_telemetry_storage_object,
)
from community_cloud_api.data_lake._ai_usage_partitioning_test_helpers import ai_usage_envelope
from community_cloud_api.data_lake._assessment_partitioning_test_helpers import assessment_envelope
from community_cloud_api.data_lake._cli_event_partitioning_test_helpers import cli_event_envelope
from community_cloud_api.data_lake._extension_event_partitioning_test_helpers import (
    extension_event_envelope,
)
from community_cloud_api.data_lake._quarantine_test_helpers import make_quarantine_record
from community_cloud_api.data_lake._telemetry_partitioning_test_helpers import telemetry_envelope
from community_cloud_api.ai_usage_helpers import valid_ai_usage_body
from community_cloud_api.assessment_metadata_helpers import valid_assessment_metadata_body
from community_cloud_api.cli_event_helpers import valid_cli_event_body
from community_cloud_api.extension_event_helpers import valid_extension_event_body
from community_cloud_api.telemetry_helpers import valid_telemetry_body

from verification.community_data_lake.contract import ACCEPTED_STREAMS, FIXED_ACCEPTANCE_UTC

VERIFICATION_CLOCK = FixedAcceptanceClock(datetime.fromisoformat(FIXED_ACCEPTANCE_UTC))

_STREAM_ENVELOPE_BUILDERS: dict[str, Any] = {
    "telemetry": telemetry_envelope,
    "assessment_metadata": assessment_envelope,
    "cli_event": cli_event_envelope,
    "extension_event": extension_event_envelope,
    "ai_usage": ai_usage_envelope,
}

_STREAM_PROJECTORS: dict[str, Any] = {
    "telemetry": project_telemetry_storage_object,
    "assessment_metadata": project_assessment_metadata_storage_object,
    "cli_event": project_cli_event_storage_object,
    "extension_event": project_extension_event_storage_object,
    "ai_usage": project_ai_usage_storage_object,
}

_STREAM_EVENT_KEYS: dict[str, str] = {
    "telemetry": "event:sv9-telemetry-key",
    "assessment_metadata": "event:sv9-assessment-key",
    "cli_event": "event:sv9-cli-event-key",
    "extension_event": "event:sv9-extension-key",
    "ai_usage": "event:sv9-ai-usage-key",
}

_STREAM_SAFE_REFS: dict[str, str] = {
    "telemetry": "evt-sv9telemetry01",
    "assessment_metadata": "evt-sv9assessment1",
    "cli_event": "evt-sv9clievent01",
    "extension_event": "evt-sv9extension1",
    "ai_usage": "evt-sv9aiusage001",
}

_STREAM_EVENT_IDS: dict[str, str] = {
    "telemetry": "evt-sv9-telemetry-001",
    "assessment_metadata": "amd-sv9-assessment-001",
    "cli_event": "cli-sv9-event-0001",
    "extension_event": "ext-sv9-event-0001",
    "ai_usage": "aiu-sv9-usage-00001",
}

CONFLICT_EVENT_KEY = "event:sv9-conflict-key"


def build_stream_envelope(stream: str, **overrides: Any) -> Any:
    builder = _STREAM_ENVELOPE_BUILDERS[stream]
    base = {
        "event_key": _STREAM_EVENT_KEYS[stream],
        "safe_event_reference": _STREAM_SAFE_REFS[stream],
        "clock": VERIFICATION_CLOCK,
        "event_id": _STREAM_EVENT_IDS[stream],
    }
    base.update(overrides)
    return builder(**base)


def project_stream_storage_object(stream: str, **overrides: Any) -> ImmutableRawStorageObject:
    envelope = build_stream_envelope(stream, **overrides)
    projection = _STREAM_PROJECTORS[stream](envelope)
    return projection.storage_object


def _project_conflict_envelope(
    stream: str,
    *,
    request: Any,
) -> ImmutableRawStorageObject:
    envelope = build_data_lake_envelope(
        event_stream=stream,
        request=request,
        event_key=CONFLICT_EVENT_KEY,
        safe_event_reference="evt-sv9conflict01",
        clock=VERIFICATION_CLOCK,
    )
    return _STREAM_PROJECTORS[stream](envelope).storage_object


def project_conflict_storage_object(stream: str) -> ImmutableRawStorageObject:
    """Same identity key, different canonical bytes — for CONFLICT scenarios."""

    common = {
        "event_key": CONFLICT_EVENT_KEY,
        "safe_event_reference": "evt-sv9conflict01",
        "clock": VERIFICATION_CLOCK,
    }
    if stream == "telemetry":
        return project_stream_storage_object(
            stream,
            **common,
            event_id="evt-sv9-conflict-a",
            event_type="operation_failed",
        )
    if stream == "assessment_metadata":
        body = valid_assessment_metadata_body(event_id="amd-sv9-conflict-a")
        body["assessment"] = {**body["assessment"], "finding_count": 99}
        request = AssessmentMetadataRequest.model_validate(body)
        envelope = build_data_lake_envelope(
            event_stream="assessment_metadata",
            request=request,
            event_key=CONFLICT_EVENT_KEY,
            safe_event_reference="evt-sv9conflict01",
            clock=VERIFICATION_CLOCK,
        )
        return project_assessment_metadata_storage_object(envelope).storage_object
    if stream == "cli_event":
        body = valid_cli_event_body(event_id="cli-sv9-conflict-a")
        body["event"] = {**body["event"], "duration_bucket": "over_10m"}
        return _project_conflict_envelope(
            stream, request=CliEventRequest.model_validate(body)
        )
    if stream == "extension_event":
        body = valid_extension_event_body(event_id="ext-sv9-conflict-a")
        body["event"] = {**body["event"], "duration_bucket": "over_10m"}
        return _project_conflict_envelope(
            stream, request=ExtensionEventRequest.model_validate(body)
        )
    if stream == "ai_usage":
        body = valid_ai_usage_body(event_id="aiu-sv9-conflict-a")
        body["usage"] = {**body["usage"], "duration_bucket": "over_10m"}
        return _project_conflict_envelope(stream, request=AiUsageRequest.model_validate(body))
    raise KeyError(stream)


def project_conflict_peer(stream: str) -> ImmutableRawStorageObject:
    """Second object with same key as :func:`project_conflict_storage_object`."""

    common = {
        "event_key": CONFLICT_EVENT_KEY,
        "safe_event_reference": "evt-sv9conflict01",
        "clock": VERIFICATION_CLOCK,
    }
    if stream == "telemetry":
        return project_stream_storage_object(
            stream,
            **common,
            event_id="evt-sv9-conflict-b",
            event_type="application_started",
        )
    if stream == "assessment_metadata":
        body = valid_assessment_metadata_body(event_id="amd-sv9-conflict-b")
        body["assessment"] = {**body["assessment"], "finding_count": 1}
        request = AssessmentMetadataRequest.model_validate(body)
        envelope = build_data_lake_envelope(
            event_stream="assessment_metadata",
            request=request,
            event_key=CONFLICT_EVENT_KEY,
            safe_event_reference="evt-sv9conflict01",
            clock=VERIFICATION_CLOCK,
        )
        return project_assessment_metadata_storage_object(envelope).storage_object
    if stream == "cli_event":
        body = valid_cli_event_body(event_id="cli-sv9-conflict-b")
        body["event"] = {**body["event"], "duration_bucket": "5s_to_30s"}
        return _project_conflict_envelope(
            stream, request=CliEventRequest.model_validate(body)
        )
    if stream == "extension_event":
        body = valid_extension_event_body(event_id="ext-sv9-conflict-b")
        body["event"] = {**body["event"], "duration_bucket": "5s_to_30s"}
        return _project_conflict_envelope(
            stream, request=ExtensionEventRequest.model_validate(body)
        )
    if stream == "ai_usage":
        body = valid_ai_usage_body(event_id="aiu-sv9-conflict-b")
        body["usage"] = {**body["usage"], "duration_bucket": "1s_to_5s"}
        return _project_conflict_envelope(stream, request=AiUsageRequest.model_validate(body))
    raise KeyError(stream)


def project_all_streams() -> dict[str, ImmutableRawStorageObject]:
    return {stream: project_stream_storage_object(stream) for stream in ACCEPTED_STREAMS}


def build_quarantine_record(**overrides: Any) -> Any:
    base = {"clock": VERIFICATION_CLOCK}
    base.update(overrides)
    return make_quarantine_record(**base)


def project_quarantine_object(**overrides: Any) -> ImmutableQuarantineStorageObject:
    return build_quarantine_storage_object(build_quarantine_record(**overrides))


__all__ = [
    "CONFLICT_EVENT_KEY",
    "VERIFICATION_CLOCK",
    "build_quarantine_record",
    "build_stream_envelope",
    "project_all_streams",
    "project_conflict_peer",
    "project_conflict_storage_object",
    "project_quarantine_object",
    "project_stream_storage_object",
]

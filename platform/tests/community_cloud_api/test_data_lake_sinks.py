"""Unit tests for Data Lake-backed ingestion sinks (Slice 17.7)."""

from __future__ import annotations

from datetime import datetime, timezone

from codestrata_platform.community_cloud_api.data_lake.accepted_clock import FixedAcceptanceClock
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore
from codestrata_platform.community_cloud_api.data_lake.sinks import (
    DataLakeTelemetryEventSink,
)
from codestrata_platform.community_cloud_api.telemetry.enums import TelemetrySinkStatus
from codestrata_platform.community_cloud_api.telemetry.ports import ValidatedTelemetryEvent

from .data_lake._request_test_helpers import make_cli_event_request, make_telemetry_request


def _validated_telemetry(request) -> ValidatedTelemetryEvent:
    return ValidatedTelemetryEvent(
        event_key="event:abcdef123456789012345678",
        safe_event_reference="evt-aaaaaaaaaaaa",
        schema_version=request.schema_version,
        event_type=request.event_type,
        client=request.client,
        occurred_at=getattr(request, "occurred_at", None),
        properties=getattr(request, "properties", None),
        payload_fingerprint="fp:" + ("a" * 64),
        identity_policy_version="1.0",
        telemetry_policy_version="community-telemetry-policy:1.0",
    )


def test_data_lake_telemetry_sink_accepts_with_request() -> None:
    store = InMemoryCommunityDataLakeStore()
    clock = FixedAcceptanceClock(datetime(2026, 8, 3, tzinfo=timezone.utc))
    sink = DataLakeTelemetryEventSink(store=store, clock=clock)
    request = make_telemetry_request()
    event = _validated_telemetry(request)

    result = sink.accept(event, request=request)

    assert result.status is TelemetrySinkStatus.ACCEPTED
    assert len(store.accepted_object_keys()) >= 1


def test_data_lake_telemetry_sink_unavailable_without_request() -> None:
    store = InMemoryCommunityDataLakeStore()
    sink = DataLakeTelemetryEventSink(store=store)
    request = make_telemetry_request()
    event = _validated_telemetry(request)

    result = sink.accept(event)

    assert result.status is TelemetrySinkStatus.UNAVAILABLE
    assert store.accepted_object_keys() == ()


def test_data_lake_telemetry_sink_quarantines_on_stream_mismatch() -> None:
    store = InMemoryCommunityDataLakeStore()
    clock = FixedAcceptanceClock(datetime(2026, 8, 3, tzinfo=timezone.utc))
    sink = DataLakeTelemetryEventSink(store=store, clock=clock)
    request = make_telemetry_request()
    event = _validated_telemetry(request)
    wrong = make_cli_event_request()

    result = sink.accept(event, request=wrong)

    assert result.status is TelemetrySinkStatus.REJECTED
    assert len(store.quarantined_object_keys()) >= 1

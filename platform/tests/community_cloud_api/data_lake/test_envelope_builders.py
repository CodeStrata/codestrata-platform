"""High-level typed envelope builder tests (Slice 8.3)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from codestrata_platform.community_cloud_api.data_lake.accepted_clock import FixedAcceptanceClock
from codestrata_platform.community_cloud_api.data_lake.envelope_builders import (
    build_data_lake_envelope,
    build_storage_object_from_request,
    put_request_via_store,
)
from codestrata_platform.community_cloud_api.data_lake.envelope_models import EnvelopeErrorCode
from codestrata_platform.community_cloud_api.data_lake.envelope_validation import EnvelopeBuildError
from codestrata_platform.community_cloud_api.data_lake.envelopes import DataLakeEnvelope
from codestrata_platform.community_cloud_api.data_lake.objects import ImmutableRawStorageObject
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.ports import (
    InMemoryCommunityDataLakeStore,
    StorageWriteResult,
)

from ._request_test_helpers import (
    make_ai_usage_request,
    make_assessment_metadata_request,
    make_cli_event_request,
    make_extension_event_request,
    make_telemetry_request,
)

_CLOCK = FixedAcceptanceClock(datetime(2026, 8, 4, 12, 34, 56, tzinfo=timezone.utc))


def test_build_data_lake_envelope_succeeds_for_telemetry() -> None:
    envelope = build_data_lake_envelope(
        event_stream="telemetry",
        request=make_telemetry_request(),
        event_key="event:abcdef1234567890abcdef12",
        safe_event_reference="evt-aaaaaaaaaaaa",
        clock=_CLOCK,
    )
    assert isinstance(envelope, DataLakeEnvelope)
    assert envelope.event_stream == "telemetry"
    assert envelope.source_contract.schema_name == "community-telemetry"
    assert envelope.acceptance.accepted_at == "2026-08-04T12:34:56Z"
    assert envelope.acceptance.partition_date == "2026-08-04"
    assert envelope.client.client_type == "codestrata_cli"
    assert envelope.payload["event_id"] == "evt-test-0001"


@pytest.mark.parametrize(
    "event_stream,make_request",
    [
        ("assessment_metadata", make_assessment_metadata_request),
        ("cli_event", make_cli_event_request),
        ("extension_event", make_extension_event_request),
        ("ai_usage", make_ai_usage_request),
    ],
)
def test_build_data_lake_envelope_succeeds_for_every_other_stream(
    event_stream: str, make_request
) -> None:
    envelope = build_data_lake_envelope(
        event_stream=event_stream,
        request=make_request(),
        event_key=f"event:{event_stream}0000000000000000",
        safe_event_reference="evt-bbbbbbbbbbbb",
        clock=_CLOCK,
    )
    assert envelope.event_stream == event_stream


def test_build_data_lake_envelope_rejects_unknown_event_stream() -> None:
    with pytest.raises(EnvelopeBuildError) as excinfo:
        build_data_lake_envelope(
            event_stream="not_a_real_stream",
            request=make_telemetry_request(),
            event_key="event:abcdef1234567890abcdef12",
            safe_event_reference="evt-aaaaaaaaaaaa",
            clock=_CLOCK,
        )
    assert excinfo.value.code is EnvelopeErrorCode.INVALID_ENVELOPE


def test_build_data_lake_envelope_rejects_stream_request_mismatch() -> None:
    with pytest.raises(EnvelopeBuildError) as excinfo:
        build_data_lake_envelope(
            event_stream="cli_event",
            request=make_telemetry_request(),
            event_key="event:abcdef1234567890abcdef12",
            safe_event_reference="evt-aaaaaaaaaaaa",
            clock=_CLOCK,
        )
    assert excinfo.value.code is EnvelopeErrorCode.STREAM_CONTRACT_MISMATCH


@pytest.mark.parametrize(
    "event_stream,make_request",
    [
        ("telemetry", make_assessment_metadata_request),
        ("assessment_metadata", make_cli_event_request),
        ("cli_event", make_extension_event_request),
        ("extension_event", make_ai_usage_request),
        ("ai_usage", make_telemetry_request),
    ],
)
def test_build_data_lake_envelope_cross_rejects_every_stream_pairing(
    event_stream: str, make_request
) -> None:
    with pytest.raises(EnvelopeBuildError) as excinfo:
        build_data_lake_envelope(
            event_stream=event_stream,
            request=make_request(),
            event_key="event:abcdef1234567890abcdef12",
            safe_event_reference="evt-aaaaaaaaaaaa",
            clock=_CLOCK,
        )
    assert excinfo.value.code is EnvelopeErrorCode.STREAM_CONTRACT_MISMATCH


def test_build_data_lake_envelope_uses_clock_for_acceptance_time() -> None:
    other_clock = FixedAcceptanceClock(datetime(2020, 1, 2, 3, 4, 5, tzinfo=timezone.utc))
    envelope = build_data_lake_envelope(
        event_stream="telemetry",
        request=make_telemetry_request(),
        event_key="event:abcdef1234567890abcdef12",
        safe_event_reference="evt-aaaaaaaaaaaa",
        clock=other_clock,
    )
    assert envelope.acceptance.accepted_at == "2020-01-02T03:04:05Z"
    assert envelope.acceptance.partition_date == "2020-01-02"


def test_build_data_lake_envelope_rejects_oversized_serialized_envelope() -> None:
    tight_policy = CommunityDataLakePolicy(max_envelope_bytes=1024)
    with pytest.raises(EnvelopeBuildError) as excinfo:
        build_data_lake_envelope(
            event_stream="assessment_metadata",
            request=make_assessment_metadata_request(),
            event_key="event:abcdef1234567890abcdef12",
            safe_event_reference="evt-aaaaaaaaaaaa",
            clock=_CLOCK,
            policy=tight_policy,
        )
    assert excinfo.value.code is EnvelopeErrorCode.ENVELOPE_TOO_LARGE


def test_build_storage_object_from_request_returns_resolved_object() -> None:
    storage_object = build_storage_object_from_request(
        event_stream="telemetry",
        request=make_telemetry_request(),
        event_key="event:abcdef1234567890abcdef12",
        safe_event_reference="evt-aaaaaaaaaaaa",
        clock=_CLOCK,
    )
    assert isinstance(storage_object, ImmutableRawStorageObject)
    assert storage_object.event_stream == "telemetry"


def test_put_request_via_store_writes_through_to_the_store() -> None:
    store = InMemoryCommunityDataLakeStore()
    result = put_request_via_store(
        store,
        event_stream="telemetry",
        request=make_telemetry_request(),
        event_key="event:abcdef1234567890abcdef12",
        safe_event_reference="evt-aaaaaaaaaaaa",
        clock=_CLOCK,
    )
    assert isinstance(result, StorageWriteResult)
    assert result.status.value == "stored"


def test_put_request_via_store_is_idempotent_for_identical_replay() -> None:
    store = InMemoryCommunityDataLakeStore()
    kwargs = dict(
        event_stream="telemetry",
        request=make_telemetry_request(),
        event_key="event:abcdef1234567890abcdef12",
        safe_event_reference="evt-aaaaaaaaaaaa",
        clock=_CLOCK,
    )
    first = put_request_via_store(store, **kwargs)
    second = put_request_via_store(store, **kwargs)
    assert first.status.value == "stored"
    assert second.status.value == "already_exists"


def test_envelope_build_error_to_stable_dict_bounds_detail_length() -> None:
    error = EnvelopeBuildError(EnvelopeErrorCode.INVALID_ENVELOPE, "x" * 200)
    blob = error.to_stable_dict()
    assert len(blob["detail"]) <= 64
    assert blob["code"] == "invalid_envelope"

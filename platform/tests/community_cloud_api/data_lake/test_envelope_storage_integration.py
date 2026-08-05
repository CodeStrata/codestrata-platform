"""End-to-end request -> envelope -> storage integration tests (Slice 8.3).

Exercises the full ``build_data_lake_envelope`` /
``build_storage_object_from_request`` / ``put_request_via_store`` path against
:class:`InMemoryCommunityDataLakeStore`, across every registered event
stream, without ever touching HTTP, ``app.py``, or S3.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from codestrata_platform.community_cloud_api.data_lake.accepted_clock import FixedAcceptanceClock
from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.envelope_builders import (
    build_storage_object_from_request,
    put_request_via_store,
)
from codestrata_platform.community_cloud_api.data_lake.objects import ImmutableRawStorageObject
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore

from ._request_test_helpers import (
    make_ai_usage_request,
    make_assessment_metadata_request,
    make_cli_event_request,
    make_extension_event_request,
    make_telemetry_request,
)

_CLOCK = FixedAcceptanceClock(datetime(2026, 8, 4, 9, 0, 0, tzinfo=timezone.utc))

_STREAM_CASES = [
    ("telemetry", make_telemetry_request),
    ("assessment_metadata", make_assessment_metadata_request),
    ("cli_event", make_cli_event_request),
    ("extension_event", make_extension_event_request),
    ("ai_usage", make_ai_usage_request),
]


@pytest.mark.parametrize("event_stream,make_request", _STREAM_CASES)
def test_put_request_via_store_stores_every_stream_end_to_end(event_stream: str, make_request) -> None:
    store = InMemoryCommunityDataLakeStore()
    result = put_request_via_store(
        store,
        event_stream=event_stream,
        request=make_request(),
        event_key=f"event:{event_stream}integration0",
        safe_event_reference="evt-integration01",
        clock=_CLOCK,
    )
    assert result.status is StorageWriteStatus.STORED
    assert result.object_key is not None
    assert result.object_key.startswith("raw/")
    assert result.receipt is not None


@pytest.mark.parametrize("event_stream,make_request", _STREAM_CASES)
def test_stored_object_key_never_contains_event_identity(event_stream: str, make_request) -> None:
    store = InMemoryCommunityDataLakeStore()
    event_key = f"event:{event_stream}identity000000"
    safe_reference = "evt-noleaked0001"
    result = put_request_via_store(
        store,
        event_stream=event_stream,
        request=make_request(),
        event_key=event_key,
        safe_event_reference=safe_reference,
        clock=_CLOCK,
    )
    assert event_key not in result.object_key
    assert safe_reference not in result.object_key
    assert "event:" not in result.object_key
    assert "evt-" not in result.object_key


def test_replaying_identical_request_is_idempotent_across_the_full_path() -> None:
    store = InMemoryCommunityDataLakeStore()
    kwargs = dict(
        event_stream="telemetry",
        request=make_telemetry_request(),
        event_key="event:replaystableidentity0",
        safe_event_reference="evt-replay0001",
        clock=_CLOCK,
    )
    first = put_request_via_store(store, **kwargs)
    second = put_request_via_store(store, **kwargs)
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.ALREADY_EXISTS
    assert first.object_key == second.object_key


def test_same_event_key_with_different_payload_is_a_conflict() -> None:
    store = InMemoryCommunityDataLakeStore()
    first = put_request_via_store(
        store,
        event_stream="telemetry",
        request=make_telemetry_request(event_type="application_started"),
        event_key="event:conflictsamekey00000",
        safe_event_reference="evt-conflict0001",
        clock=_CLOCK,
    )
    second = put_request_via_store(
        store,
        event_stream="telemetry",
        request=make_telemetry_request(event_type="application_completed"),
        event_key="event:conflictsamekey00000",
        safe_event_reference="evt-conflict0001",
        clock=_CLOCK,
    )
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.CONFLICT


def test_build_storage_object_from_request_produces_object_consumable_by_store() -> None:
    storage_object = build_storage_object_from_request(
        event_stream="telemetry",
        request=make_telemetry_request(),
        event_key="event:directbuild00000000",
        safe_event_reference="evt-directbuild001",
        clock=_CLOCK,
    )
    assert isinstance(storage_object, ImmutableRawStorageObject)
    store = InMemoryCommunityDataLakeStore()
    result = store.put_immutable_storage_object(storage_object)
    assert result.status is StorageWriteStatus.STORED


def test_stored_content_round_trips_through_get_accepted_content() -> None:
    store = InMemoryCommunityDataLakeStore()
    result = put_request_via_store(
        store,
        event_stream="telemetry",
        request=make_telemetry_request(),
        event_key="event:roundtripcontent000",
        safe_event_reference="evt-roundtrip0001",
        clock=_CLOCK,
    )
    stored = store.get_accepted_content(result.object_key)
    assert stored is not None
    assert stored["event_stream"] == "telemetry"
    assert stored["payload"]["event_id"] == "evt-test-0001"

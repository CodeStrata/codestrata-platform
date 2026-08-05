"""Envelope determinism tests (Slice 8.3).

Covers: identical logical construction with reversed dict insertion order
produces byte-identical canonical output; the same clock always produces
identical bytes; a different ``accepted_at`` changes the serialized bytes and
partition date but never the lake-object id (which is keyed off
``event_key``, not acceptance time).
"""

from __future__ import annotations

from datetime import datetime, timezone

from codestrata_platform.community_cloud_api.data_lake.canonical_json import (
    serialize_canonical_raw_json,
)
from codestrata_platform.community_cloud_api.data_lake.identifiers import build_lake_object_id
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy

from ._envelope_test_helpers import make_envelope

POLICY = CommunityDataLakePolicy.default()


def test_reversed_payload_insertion_order_produces_identical_canonical_bytes() -> None:
    forward = make_envelope(payload={"a": 1, "b": 2, "nested": {"y": 1, "z": 2}})
    reversed_payload = {"nested": {"z": 2, "y": 1}, "b": 2, "a": 1}
    backward = make_envelope(payload=reversed_payload)
    assert (
        serialize_canonical_raw_json(forward).data == serialize_canonical_raw_json(backward).data
    )


def test_reversed_payload_insertion_order_produces_identical_digest() -> None:
    forward = make_envelope(payload={"a": 1, "b": 2})
    backward = make_envelope(payload={"b": 2, "a": 1})
    assert (
        serialize_canonical_raw_json(forward).content_sha256
        == serialize_canonical_raw_json(backward).content_sha256
    )


def test_same_clock_and_inputs_produce_identical_bytes() -> None:
    kwargs = dict(
        event_key="event:determinismstable0",
        safe_event_reference="evt-stable0001",
        accepted_at="2026-08-04T10:00:00Z",
        payload={"duration_bucket": "1s_to_5s"},
    )
    first = make_envelope(**kwargs)
    second = make_envelope(**kwargs)
    assert serialize_canonical_raw_json(first).data == serialize_canonical_raw_json(second).data


def test_different_accepted_at_changes_serialized_bytes_and_partition_date() -> None:
    early = make_envelope(
        event_key="event:sameeventkey000000", accepted_at="2026-08-01T00:00:00Z"
    )
    late = make_envelope(event_key="event:sameeventkey000000", accepted_at="2026-08-31T23:59:59Z")
    assert serialize_canonical_raw_json(early).data != serialize_canonical_raw_json(late).data
    assert early.acceptance.partition_date == "2026-08-01"
    assert late.acceptance.partition_date == "2026-08-31"


def test_different_accepted_at_never_changes_the_lake_object_id() -> None:
    event_key = "event:sameeventkey000000"
    early = make_envelope(event_key=event_key, accepted_at="2026-08-01T00:00:00Z")
    late = make_envelope(event_key=event_key, accepted_at="2026-08-31T23:59:59Z")
    early_id = build_lake_object_id(
        POLICY.policy_token, early.event_stream, early.source_schema_version, early.event_key
    )
    late_id = build_lake_object_id(
        POLICY.policy_token, late.event_stream, late.source_schema_version, late.event_key
    )
    assert early_id == late_id


def test_different_event_key_changes_the_lake_object_id() -> None:
    a = make_envelope(event_key="event:aaaaaaaaaaaaaaaaaaaa")
    b = make_envelope(event_key="event:bbbbbbbbbbbbbbbbbbbb")
    a_id = build_lake_object_id(
        POLICY.policy_token, a.event_stream, a.source_schema_version, a.event_key
    )
    b_id = build_lake_object_id(
        POLICY.policy_token, b.event_stream, b.source_schema_version, b.event_key
    )
    assert a_id != b_id


def test_utc_normalization_of_accepted_at_via_clock_is_deterministic() -> None:
    from codestrata_platform.community_cloud_api.data_lake.accepted_clock import (
        FixedAcceptanceClock,
        format_accepted_at,
    )

    naive_like_utc = datetime(2026, 8, 4, 12, 0, 0, tzinfo=timezone.utc)
    clock = FixedAcceptanceClock(naive_like_utc)
    assert format_accepted_at(clock.now_utc()) == "2026-08-04T12:00:00Z"
    # Calling repeatedly must yield the identical formatted string.
    assert format_accepted_at(clock.now_utc()) == format_accepted_at(clock.now_utc())

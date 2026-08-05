"""Determinism guarantees across the immutable raw-JSON storage contract (Slice 8.2)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.canonical_json import (
    serialize_canonical_raw_json,
)
from codestrata_platform.community_cloud_api.data_lake.immutable_write import (
    build_immutable_raw_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore

from ._envelope_test_helpers import make_envelope

POLICY = CommunityDataLakePolicy.default()


def _envelope(**overrides: object) -> object:
    base: dict[str, object] = dict(
        safe_event_reference="evt-determinismkeya",
        event_key="event:determinism-key",
        payload={"b": 2, "a": 1, "nested": {"z": 1, "y": 2}},
    )
    base.update(overrides)
    return make_envelope(**base)  # type: ignore[arg-type]


def test_canonical_bytes_identical_across_repeated_serializations() -> None:
    envelope = _envelope()
    first = serialize_canonical_raw_json(envelope)
    second = serialize_canonical_raw_json(envelope)
    assert first.data == second.data
    assert first.content_sha256 == second.content_sha256


def test_canonical_bytes_identical_regardless_of_payload_key_insertion_order() -> None:
    envelope_a = _envelope(payload={"a": 1, "b": 2, "nested": {"y": 2, "z": 1}})
    envelope_b = _envelope(payload={"nested": {"z": 1, "y": 2}, "b": 2, "a": 1})
    canonical_a = serialize_canonical_raw_json(envelope_a)
    canonical_b = serialize_canonical_raw_json(envelope_b)
    assert canonical_a.data == canonical_b.data
    assert canonical_a.content_sha256 == canonical_b.content_sha256


def test_storage_object_deterministic_across_process_equivalent_builds() -> None:
    envelope = _envelope()
    first = build_immutable_raw_storage_object(envelope, POLICY)
    second = build_immutable_raw_storage_object(envelope, POLICY)
    assert first.object_id == second.object_id
    assert first.object_key == second.object_key
    assert first.content_sha256 == second.content_sha256
    assert first.canonical_json_bytes == second.canonical_json_bytes
    assert first.to_s3_metadata() == second.to_s3_metadata()


def test_different_event_streams_produce_different_deterministic_keys() -> None:
    telemetry_obj = build_immutable_raw_storage_object(
        _envelope(event_stream="telemetry", event_key="event:same-key-different-stream"), POLICY
    )
    cli_obj = build_immutable_raw_storage_object(
        _envelope(event_stream="cli_event", event_key="event:same-key-different-stream"), POLICY
    )
    assert telemetry_obj.object_key != cli_obj.object_key
    assert telemetry_obj.object_id != cli_obj.object_id


def test_in_memory_store_replay_is_deterministically_already_exists() -> None:
    store = InMemoryCommunityDataLakeStore()
    envelope = _envelope()
    results = [store.put_immutable_event(envelope) for _ in range(5)]
    statuses = [r.status.value for r in results]
    assert statuses[0] == "stored"
    assert all(status == "already_exists" for status in statuses[1:])
    digests = {store.get_accepted_digest(r.object_key) for r in results}
    assert len(digests) == 1


def test_canonical_json_bytes_are_valid_utf8_json_and_round_trip() -> None:
    envelope = _envelope()
    canonical = serialize_canonical_raw_json(envelope)
    import json

    round_tripped = json.loads(canonical.data.decode("utf-8"))
    assert round_tripped == envelope.to_stable_dict()

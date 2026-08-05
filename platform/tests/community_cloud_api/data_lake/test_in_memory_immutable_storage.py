"""In-memory store immutable raw-JSON storage contract tests (Slice 8.2)."""

from __future__ import annotations

import hashlib

from codestrata_platform.community_cloud_api.data_lake.canonical_json import (
    serialize_canonical_raw_json,
)
from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.immutable_write import (
    build_immutable_raw_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore

from ._envelope_test_helpers import make_envelope

POLICY = CommunityDataLakePolicy.default()


def _envelope(**overrides: object) -> object:
    base: dict[str, object] = dict(
        event_stream="extension_event",
        schema_name="community-extension-event",
        schema_version="1.0",
        policy_id="community-extension-event-policy:1.0",
        safe_event_reference="evt-inmemorykeyaaaa",
        event_key="event:in-memory-key",
        client_type="vscode_extension",
        payload={"lifecycle": "completed"},
    )
    base.update(overrides)
    return make_envelope(**base)  # type: ignore[arg-type]


def test_put_immutable_event_stored_returns_receipt() -> None:
    store = InMemoryCommunityDataLakeStore()
    result = store.put_immutable_event(_envelope())
    assert result.status is StorageWriteStatus.STORED
    assert result.receipt is not None
    assert result.receipt.status is StorageWriteStatus.STORED
    assert result.receipt.object_key == result.object_key


def test_get_accepted_bytes_matches_canonical_serialization() -> None:
    store = InMemoryCommunityDataLakeStore()
    envelope = _envelope()
    result = store.put_immutable_event(envelope)
    canonical = serialize_canonical_raw_json(envelope)
    stored_bytes = store.get_accepted_bytes(result.object_key)
    assert stored_bytes == canonical.data


def test_get_accepted_digest_matches_sha256_of_stored_bytes() -> None:
    store = InMemoryCommunityDataLakeStore()
    result = store.put_immutable_event(_envelope())
    stored_bytes = store.get_accepted_bytes(result.object_key)
    stored_digest = store.get_accepted_digest(result.object_key)
    expected = "sha256:" + hashlib.sha256(stored_bytes).hexdigest()
    assert stored_digest == expected


def test_get_accepted_bytes_returns_none_for_unknown_key() -> None:
    store = InMemoryCommunityDataLakeStore()
    assert store.get_accepted_bytes("raw/does/not/exist.json") is None


def test_get_accepted_digest_returns_none_for_unknown_key() -> None:
    store = InMemoryCommunityDataLakeStore()
    assert store.get_accepted_digest("raw/does/not/exist.json") is None


def test_get_accepted_content_still_returns_envelope_dict_slice_8_1_compat() -> None:
    store = InMemoryCommunityDataLakeStore()
    envelope = _envelope()
    result = store.put_immutable_event(envelope)
    content = store.get_accepted_content(result.object_key)
    assert content == envelope.to_stable_dict()


def test_identical_replay_is_already_exists_with_receipt() -> None:
    store = InMemoryCommunityDataLakeStore()
    first = store.put_immutable_event(_envelope())
    second = store.put_immutable_event(_envelope())
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.ALREADY_EXISTS
    assert second.receipt is not None
    assert second.receipt.status is StorageWriteStatus.ALREADY_EXISTS
    assert first.object_key == second.object_key
    # Bytes must be byte-for-byte identical to the original write, unchanged.
    assert store.get_accepted_bytes(first.object_key) == store.get_accepted_bytes(second.object_key)


def test_conflicting_payload_is_conflict_and_never_overwrites_bytes() -> None:
    store = InMemoryCommunityDataLakeStore()
    first = store.put_immutable_event(_envelope(payload={"lifecycle": "completed"}))
    original_bytes = store.get_accepted_bytes(first.object_key)
    original_digest = store.get_accepted_digest(first.object_key)

    second = store.put_immutable_event(_envelope(payload={"lifecycle": "started"}))
    assert second.status is StorageWriteStatus.CONFLICT
    assert second.receipt is None
    assert second.object_key == first.object_key

    assert store.get_accepted_bytes(first.object_key) == original_bytes
    assert store.get_accepted_digest(first.object_key) == original_digest


def test_put_immutable_storage_object_direct_path_stores_and_replays() -> None:
    store = InMemoryCommunityDataLakeStore()
    obj = build_immutable_raw_storage_object(_envelope(), POLICY)
    first = store.put_immutable_storage_object(obj)
    assert first.status is StorageWriteStatus.STORED
    second = store.put_immutable_storage_object(obj)
    assert second.status is StorageWriteStatus.ALREADY_EXISTS


def test_put_immutable_storage_object_conflict_never_overwrites() -> None:
    store = InMemoryCommunityDataLakeStore()
    first_obj = build_immutable_raw_storage_object(
        _envelope(payload={"lifecycle": "completed"}), POLICY
    )
    second_obj = build_immutable_raw_storage_object(
        _envelope(payload={"lifecycle": "started"}), POLICY
    )
    store.put_immutable_storage_object(first_obj)
    result = store.put_immutable_storage_object(second_obj)
    assert result.status is StorageWriteStatus.CONFLICT
    assert store.get_accepted_bytes(first_obj.object_key) == first_obj.canonical_json_bytes


def test_storage_write_result_to_stable_dict_includes_receipt_public_dict() -> None:
    store = InMemoryCommunityDataLakeStore()
    result = store.put_immutable_event(_envelope())
    blob = result.to_stable_dict()
    assert "receipt" in blob
    assert "object_key" not in blob["receipt"]
    assert blob["receipt"]["status"] == "stored"

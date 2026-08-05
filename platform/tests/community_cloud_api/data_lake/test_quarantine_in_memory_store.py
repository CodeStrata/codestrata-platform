"""In-memory quarantine store tests (Slice 8.9)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore
from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
    build_quarantine_storage_object,
)

from ._quarantine_test_helpers import make_quarantine_record


def test_quarantine_bytes_and_digest_helpers() -> None:
    store = InMemoryCommunityDataLakeStore()
    record = make_quarantine_record()
    result = store.quarantine_event(record)
    assert result.status is StorageWriteStatus.STORED
    key = result.object_key
    assert key is not None
    digest = store.get_quarantined_digest(key)
    raw = store.get_quarantined_bytes(key)
    assert digest is not None and digest.startswith("sha256:")
    assert raw is not None and len(raw) > 0
    content = store.get_quarantined_content(key)
    assert content is not None
    assert content["quarantine_reason"] == "unsafe_payload"


def test_put_immutable_quarantine_object_round_trip() -> None:
    store = InMemoryCommunityDataLakeStore()
    obj = build_quarantine_storage_object(make_quarantine_record())
    first = store.put_immutable_quarantine_object(obj)
    second = store.put_immutable_quarantine_object(obj)
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.ALREADY_EXISTS
    assert store.get_quarantined_digest(obj.object_key) == obj.content_sha256


def test_accepted_and_quarantine_namespaces_are_separate() -> None:
    store = InMemoryCommunityDataLakeStore()
    from ._envelope_test_helpers import make_envelope

    accepted = store.put_immutable_event(make_envelope())
    quarantined = store.quarantine_event(make_quarantine_record())
    assert accepted.object_key != quarantined.object_key
    assert accepted.object_key not in store.quarantined_object_keys()
    assert quarantined.object_key not in store.accepted_object_keys()

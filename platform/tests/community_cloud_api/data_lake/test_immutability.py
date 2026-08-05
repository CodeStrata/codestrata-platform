"""Immutability guarantees for the Community Data Lake store (Slice 8.1 / 8.9)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore

from ._envelope_test_helpers import make_envelope
from ._quarantine_test_helpers import make_quarantine_record


def _envelope(**overrides: object) -> object:
    base: dict[str, object] = dict(
        event_stream="cli_event",
        schema_name="community-cli-event",
        schema_version="1.0",
        policy_id="community-cli-event-policy:1.0",
        safe_event_reference="evt-dddddddddddd",
        event_key="event:immutable-key",
        client_type="codestrata_cli",
        payload={"operation": "assess"},
    )
    base.update(overrides)
    return make_envelope(**base)  # type: ignore[arg-type]


def test_repeated_identical_put_never_mutates_stored_content() -> None:
    store = InMemoryCommunityDataLakeStore()
    first = store.put_immutable_event(_envelope())
    original = store.get_accepted_content(first.object_key)  # type: ignore[arg-type]
    assert original is not None

    for _ in range(5):
        repeat = store.put_immutable_event(_envelope())
        assert repeat.status is StorageWriteStatus.ALREADY_EXISTS
        assert repeat.object_key == first.object_key

    unchanged = store.get_accepted_content(first.object_key)  # type: ignore[arg-type]
    assert unchanged == original


def test_conflicting_put_never_overwrites_original_content() -> None:
    store = InMemoryCommunityDataLakeStore()
    first = store.put_immutable_event(_envelope(payload={"operation": "assess"}))
    original = store.get_accepted_content(first.object_key)  # type: ignore[arg-type]

    for candidate_payload in ({"operation": "modernize"}, {"operation": "explain"}):
        conflict = store.put_immutable_event(_envelope(payload=candidate_payload))
        assert conflict.status is StorageWriteStatus.CONFLICT
        assert conflict.object_key == first.object_key

    unchanged = store.get_accepted_content(first.object_key)  # type: ignore[arg-type]
    assert unchanged == original
    assert unchanged is not None
    assert unchanged["payload"] == {"operation": "assess"}


def test_conflicting_quarantine_never_overwrites_original_content() -> None:
    store = InMemoryCommunityDataLakeStore()
    record = make_quarantine_record(
        quarantine_reason="storage_key_failure",
        diagnostic_codes=("key_validation_failed",),
        safe_event_reference="evt-eeeeeeeeeeee",
        limitations=("first_attempt",),
    )
    first = store.quarantine_event(record)
    original = store.get_quarantined_content(first.object_key)  # type: ignore[arg-type]

    conflicting = make_quarantine_record(
        quarantine_reason="storage_key_failure",
        diagnostic_codes=("key_validation_failed",),
        safe_event_reference="evt-eeeeeeeeeeee",
        limitations=("second_attempt",),
    )
    result = store.quarantine_event(conflicting)
    assert result.status is StorageWriteStatus.CONFLICT
    assert result.object_key == first.object_key

    unchanged = store.get_quarantined_content(first.object_key)  # type: ignore[arg-type]
    assert unchanged == original


def test_get_accepted_content_returns_a_copy_not_a_live_reference() -> None:
    store = InMemoryCommunityDataLakeStore()
    result = store.put_immutable_event(_envelope())
    snapshot = store.get_accepted_content(result.object_key)  # type: ignore[arg-type]
    assert snapshot is not None
    snapshot["payload"] = {"tampered": True}  # mutate the caller's copy only

    fresh = store.get_accepted_content(result.object_key)  # type: ignore[arg-type]
    assert fresh is not None
    assert fresh["payload"] != {"tampered": True}


def test_different_logical_events_never_collide() -> None:
    store = InMemoryCommunityDataLakeStore()
    first = store.put_immutable_event(_envelope(event_key="event:key-one"))
    second = store.put_immutable_event(_envelope(event_key="event:key-two"))
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.STORED
    assert first.object_key != second.object_key
    assert len(store.accepted_object_keys()) == 2

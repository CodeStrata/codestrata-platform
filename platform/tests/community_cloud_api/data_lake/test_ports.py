"""Community Data Lake store port and in-memory adapter tests (Slice 8.1 / 8.9)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.ports import (
    InMemoryCommunityDataLakeStore,
    StorageWriteResult,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_models import QuarantineRecord

from ._envelope_test_helpers import make_envelope
from ._quarantine_test_helpers import make_quarantine_record


def _envelope(**overrides: object) -> object:
    return make_envelope(**overrides)  # type: ignore[arg-type]


def test_put_immutable_event_stores_new_object() -> None:
    store = InMemoryCommunityDataLakeStore()
    result = store.put_immutable_event(_envelope())
    assert result.status is StorageWriteStatus.STORED
    assert result.object_key is not None
    assert result.object_key.startswith("raw/stream=telemetry/")
    assert store.accepted_object_keys() == (result.object_key,)


def test_put_immutable_event_identical_replay_is_already_exists() -> None:
    store = InMemoryCommunityDataLakeStore()
    first = store.put_immutable_event(_envelope())
    second = store.put_immutable_event(_envelope())
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.ALREADY_EXISTS
    assert first.object_key == second.object_key
    assert len(store.accepted_object_keys()) == 1


def test_put_immutable_event_conflict_on_same_identity_different_payload() -> None:
    store = InMemoryCommunityDataLakeStore()
    first = store.put_immutable_event(_envelope(payload={"duration_bucket": "1s_to_5s"}))
    second = store.put_immutable_event(_envelope(payload={"duration_bucket": "over_10m"}))
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.CONFLICT
    assert first.object_key == second.object_key
    stored = store.get_accepted_content(first.object_key)  # type: ignore[arg-type]
    assert stored is not None
    assert stored["payload"] == {"duration_bucket": "1s_to_5s"}


def test_put_immutable_event_unavailable_store() -> None:
    store = InMemoryCommunityDataLakeStore(unavailable=True)
    result = store.put_immutable_event(_envelope())
    assert result.status is StorageWriteStatus.UNAVAILABLE
    assert result.object_key is None
    assert store.accepted_object_keys() == ()


def test_quarantine_event_stores_new_record() -> None:
    store = InMemoryCommunityDataLakeStore()
    record = make_quarantine_record(
        quarantine_reason="invalid_envelope",
        diagnostic_codes=("invalid_envelope",),
        safe_event_reference="evt-bbbbbbbbbbbb",
    )
    result = store.quarantine_event(record)
    assert result.status is StorageWriteStatus.STORED
    assert result.object_key is not None
    assert result.object_key.startswith("quarantine/reason=invalid_envelope/")
    assert store.quarantined_object_keys() == (result.object_key,)
    assert result.quarantine_receipt is not None


def test_quarantine_event_identical_replay_is_already_exists() -> None:
    store = InMemoryCommunityDataLakeStore()
    record = make_quarantine_record()
    first = store.quarantine_event(record)
    second = store.quarantine_event(record)
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.ALREADY_EXISTS
    assert first.object_key == second.object_key


def test_quarantine_event_conflict_when_non_identity_fields_differ() -> None:
    """Same identity material → same key; different limitations → CONFLICT."""

    store = InMemoryCommunityDataLakeStore()
    first = store.quarantine_event(
        make_quarantine_record(
            quarantine_reason="serialization_failure",
            diagnostic_codes=("serialization_failure",),
            safe_event_reference="evt-cccccccccccc",
            limitations=("first_limitation",),
        )
    )
    second = store.quarantine_event(
        make_quarantine_record(
            quarantine_reason="serialization_failure",
            diagnostic_codes=("serialization_failure",),
            safe_event_reference="evt-cccccccccccc",
            limitations=("second_limitation",),
        )
    )
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.CONFLICT
    assert first.object_key == second.object_key
    stored = store.get_quarantined_content(first.object_key)  # type: ignore[arg-type]
    assert stored is not None
    assert stored["limitations"] == ["first_limitation"]


def test_quarantine_event_unavailable_store() -> None:
    store = InMemoryCommunityDataLakeStore(unavailable=True)
    record = make_quarantine_record(
        quarantine_reason="storage_rejected",
        diagnostic_codes=("storage_rejected",),
    )
    result = store.quarantine_event(record)
    assert result.status is StorageWriteStatus.UNAVAILABLE
    assert store.quarantined_object_keys() == ()


def test_quarantine_event_rejects_invalid_reason() -> None:
    store = InMemoryCommunityDataLakeStore()
    record = QuarantineRecord(
        quarantine_reason="not_a_real_reason",
        validation_stage="envelope_validation",
        quarantine_reference="qz-aaaaaaaaaaaaaaaa",
        detected_at="2026-08-03T12:00:00Z",
        year="2026",
        month="08",
        day="03",
    )
    result = store.quarantine_event(record)
    assert result.status is StorageWriteStatus.REJECTED
    assert result.detail  # bounded diagnostic, exception type name only
    assert store.quarantined_object_keys() == ()


def test_quarantine_event_rejects_invalid_partition_date() -> None:
    store = InMemoryCommunityDataLakeStore()
    record = QuarantineRecord(
        quarantine_reason="invalid_envelope",
        validation_stage="envelope_validation",
        quarantine_reference="qz-bbbbbbbbbbbbbbbb",
        detected_at="2026-08-03T12:00:00Z",
        year="26",
        month="13",
        day="99",
    )
    result = store.quarantine_event(record)
    assert result.status is StorageWriteStatus.REJECTED


def test_store_clear_resets_both_object_spaces() -> None:
    store = InMemoryCommunityDataLakeStore()
    store.put_immutable_event(_envelope())
    store.quarantine_event(make_quarantine_record())
    assert store.accepted_object_keys() != ()
    assert store.quarantined_object_keys() != ()
    store.clear()
    assert store.accepted_object_keys() == ()
    assert store.quarantined_object_keys() == ()


def test_storage_write_result_to_stable_dict_omits_blank_optional_fields() -> None:
    result = StorageWriteResult(status=StorageWriteStatus.STORED, object_key="raw/x.json")
    blob = result.to_stable_dict()
    assert blob == {"object_key": "raw/x.json", "status": "stored"}


def test_quarantine_record_to_stable_dict_is_sorted() -> None:
    record = make_quarantine_record(diagnostic_codes=("size_limit_exceeded", "unsafe_payload"))
    blob = record.to_stable_dict()
    assert list(blob) == sorted(blob)
    assert blob["diagnostic_codes"] == ["size_limit_exceeded", "unsafe_payload"]

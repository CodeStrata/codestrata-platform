"""In-memory vs FakeS3 storage adapter parity tests (Slice 8.13)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from codestrata_platform.community_cloud_api.data_lake.enums import StorageClass, StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.immutable_write import (
    build_immutable_raw_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3DataLakeStoreConfiguration,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.s3_store import (
    CommunityDataLakeS3Store,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.ports import (
    InMemoryCommunityDataLakeStore,
    StorageWriteResult,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
    build_quarantine_storage_object,
)

from community_cloud_api.data_lake.test_s3_store import FakeS3Client, _client_error

from ._envelope_test_helpers import make_envelope
from ._quarantine_test_helpers import make_quarantine_record

POLICY = CommunityDataLakePolicy.default()
S3_CONFIG = S3DataLakeStoreConfiguration(bucket_name="valid-bucket-name")


def _accepted_object(**overrides: object) -> object:
    envelope = make_envelope(**overrides)  # type: ignore[arg-type]
    return build_immutable_raw_storage_object(envelope, POLICY)


def _quarantine_object(**overrides: object) -> object:
    return build_quarantine_storage_object(make_quarantine_record(**overrides))  # type: ignore[arg-type]


def _in_memory_store(*, unavailable: bool = False) -> InMemoryCommunityDataLakeStore:
    return InMemoryCommunityDataLakeStore(policy=POLICY, unavailable=unavailable)


def _s3_store(client: FakeS3Client) -> CommunityDataLakeS3Store:
    return CommunityDataLakeS3Store(config=S3_CONFIG, policy=POLICY, client=client)


def _run_accepted_scenario(store_factory: Callable[[], Any]) -> None:
    store = store_factory()
    obj = _accepted_object()
    first = store.put_immutable_storage_object(obj)
    second = store.put_immutable_storage_object(obj)
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.ALREADY_EXISTS
    assert first.storage_class is StorageClass.ACCEPTED

    first_obj = _accepted_object(event_key="event:parity-conflict-key")
    conflict_obj = _accepted_object(
        event_key="event:parity-conflict-key",
        payload={"duration_bucket": "gt_5s"},
    )
    store.put_immutable_storage_object(first_obj)
    conflict = store.put_immutable_storage_object(conflict_obj)
    assert conflict.status is StorageWriteStatus.CONFLICT


def _run_quarantine_scenario(
    store_factory: Callable[[], Any],
    *,
    unavailable: bool = False,
) -> None:
    store = store_factory()
    obj = _quarantine_object()
    first = store.put_immutable_quarantine_object(obj)
    second = store.put_immutable_quarantine_object(obj)
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.ALREADY_EXISTS
    assert first.storage_class is StorageClass.QUARANTINE

    conflict_obj = _quarantine_object(limitations=("different",))
    conflict = store.put_immutable_quarantine_object(conflict_obj)
    assert conflict.status is StorageWriteStatus.CONFLICT


def test_in_memory_accepted_parity() -> None:
    _run_accepted_scenario(_in_memory_store)


def test_s3_accepted_parity() -> None:
    _run_accepted_scenario(lambda: _s3_store(FakeS3Client()))


def test_in_memory_quarantine_parity() -> None:
    _run_quarantine_scenario(_in_memory_store)


def test_s3_quarantine_parity() -> None:
    _run_quarantine_scenario(lambda: _s3_store(FakeS3Client()))


def test_in_memory_unavailable_never_stored() -> None:
    store = _in_memory_store(unavailable=True)
    accepted = store.put_immutable_storage_object(_accepted_object())
    quarantine = store.put_immutable_quarantine_object(_quarantine_object())
    assert accepted.status is StorageWriteStatus.UNAVAILABLE
    assert quarantine.status is StorageWriteStatus.UNAVAILABLE
    assert accepted.status is not StorageWriteStatus.STORED
    assert quarantine.status is not StorageWriteStatus.STORED


def test_s3_unavailable_on_persistent_transient_error() -> None:
    def always_slow(_count: int, _kwargs: dict[str, Any]) -> Exception:
        return _client_error("SlowDown")

    client = FakeS3Client(put_behavior=always_slow)
    store = _s3_store(client)
    result = store.put_immutable_storage_object(_accepted_object())
    assert result.status is StorageWriteStatus.UNAVAILABLE
    assert result.status is not StorageWriteStatus.STORED


def test_both_adapters_reject_wrong_types() -> None:
    quarantine_obj = _quarantine_object()
    accepted_obj = _accepted_object()

    for store in (_in_memory_store(), _s3_store(FakeS3Client())):
        rejected_accepted = store.put_immutable_storage_object(quarantine_obj)  # type: ignore[arg-type]
        rejected_quarantine = store.put_immutable_quarantine_object(accepted_obj)  # type: ignore[arg-type]
        assert rejected_accepted.status is StorageWriteStatus.REJECTED
        assert rejected_quarantine.status is StorageWriteStatus.REJECTED


def test_in_memory_preserves_extra_s3_metadata_bytes_exact() -> None:
    store = _in_memory_store()
    obj = _accepted_object()
    result: StorageWriteResult = store.put_immutable_storage_object(obj)
    stored_bytes = store.get_accepted_bytes(result.object_key)
    assert stored_bytes == obj.canonical_json_bytes
    assert store.get_accepted_extra_s3_metadata(result.object_key) == dict(
        obj.extra_s3_metadata
    )


def test_s3_preserves_metadata_on_put() -> None:
    client = FakeS3Client()
    store = _s3_store(client)
    obj = _accepted_object()
    result = store.put_immutable_storage_object(obj)
    assert result.status is StorageWriteStatus.STORED
    stored = client.objects[result.object_key]
    assert stored["Body"] == obj.canonical_json_bytes
    assert stored["Metadata"] == obj.to_s3_metadata()

"""Focused negative scenario integration tests (Slice 8.14)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore

from verification.community_data_lake.inputs import (
    project_quarantine_object,
    project_stream_storage_object,
)


def test_rejected_wrong_object_types() -> None:
    store = InMemoryCommunityDataLakeStore()
    accepted = project_stream_storage_object("telemetry")
    quarantine = project_quarantine_object()
    assert store.put_immutable_storage_object(quarantine).status is StorageWriteStatus.REJECTED  # type: ignore[arg-type]
    assert store.put_immutable_quarantine_object(accepted).status is StorageWriteStatus.REJECTED  # type: ignore[arg-type]


def test_unavailable_store_never_stored() -> None:
    from codestrata_platform.community_cloud_api.data_lake.storage_factory import (
        create_community_data_lake_store,
    )

    store = create_community_data_lake_store()
    obj = project_stream_storage_object("telemetry")
    result = store.put_immutable_storage_object(obj)
    assert result.status is StorageWriteStatus.UNAVAILABLE

"""Unavailable storage adapter tests (Slice 8.13)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.enums import StorageClass, StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.immutable_write import (
    build_immutable_raw_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.unavailable_store import (
    UnavailableCommunityDataLakeStore,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
    build_quarantine_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.storage_factory import (
    create_community_data_lake_store,
)

from ._envelope_test_helpers import make_envelope
from ._quarantine_test_helpers import make_quarantine_record

POLICY = CommunityDataLakePolicy.default()


def test_factory_default_has_no_side_effects() -> None:
    store = create_community_data_lake_store()
    assert isinstance(store, UnavailableCommunityDataLakeStore)
    envelope = make_envelope()
    storage_object = build_immutable_raw_storage_object(envelope, POLICY)
    result = store.put_immutable_storage_object(storage_object)
    assert result.status is StorageWriteStatus.UNAVAILABLE
    assert result.status is not StorageWriteStatus.STORED
    assert result.detail == "store_unavailable"


def test_unavailable_never_reports_stored_for_accepted_or_quarantine() -> None:
    store = UnavailableCommunityDataLakeStore()
    accepted = store.put_immutable_storage_object(
        build_immutable_raw_storage_object(make_envelope(), POLICY)
    )
    quarantine = store.put_immutable_quarantine_object(
        build_quarantine_storage_object(make_quarantine_record())
    )
    for result, expected_class in (
        (accepted, StorageClass.ACCEPTED),
        (quarantine, StorageClass.QUARANTINE),
    ):
        assert result.status is StorageWriteStatus.UNAVAILABLE
        assert result.status is not StorageWriteStatus.STORED
        assert result.storage_class is expected_class


def test_unavailable_envelope_helpers_also_unavailable() -> None:
    store = UnavailableCommunityDataLakeStore()
    event_result = store.put_immutable_event(make_envelope())
    quarantine_result = store.quarantine_event(make_quarantine_record())
    assert event_result.status is StorageWriteStatus.UNAVAILABLE
    assert quarantine_result.status is StorageWriteStatus.UNAVAILABLE


def test_wrong_types_return_rejected_not_unavailable() -> None:
    store = UnavailableCommunityDataLakeStore()
    quarantine_obj = build_quarantine_storage_object(make_quarantine_record())
    accepted_obj = build_immutable_raw_storage_object(make_envelope(), POLICY)
    rejected_accepted = store.put_immutable_storage_object(quarantine_obj)  # type: ignore[arg-type]
    rejected_quarantine = store.put_immutable_quarantine_object(accepted_obj)  # type: ignore[arg-type]
    assert rejected_accepted.status is StorageWriteStatus.REJECTED
    assert rejected_quarantine.status is StorageWriteStatus.REJECTED


def test_unavailable_capabilities_advertised() -> None:
    store = UnavailableCommunityDataLakeStore()
    assert store.capabilities.is_unavailable is True
    assert store.capabilities.accepted_write_supported is False

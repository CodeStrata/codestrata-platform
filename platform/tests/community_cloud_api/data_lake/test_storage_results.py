"""Storage write result serialization tests (Slice 8.13)."""

from __future__ import annotations

import json

from codestrata_platform.community_cloud_api.data_lake.enums import StorageClass, StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.ports import StorageWriteResult
from codestrata_platform.community_cloud_api.data_lake.receipts import build_receipt_from_object
from codestrata_platform.community_cloud_api.data_lake.storage_results import (
    ALLOWED_STORAGE_WRITE_STATUSES,
    storage_result_to_public_dict,
)

from ._envelope_test_helpers import make_envelope


def test_to_public_dict_omits_object_key() -> None:
    result = StorageWriteResult(
        status=StorageWriteStatus.STORED,
        object_key="raw/stream=telemetry/year=2026/month=08/day=04/secret.json",
        storage_class=StorageClass.ACCEPTED,
    )
    public = result.to_public_dict()
    assert "object_key" not in public
    assert public["status"] == "stored"
    assert public["storage_class"] == "accepted"


def test_storage_result_to_public_dict_helper_matches_method() -> None:
    result = StorageWriteResult(
        status=StorageWriteStatus.ALREADY_EXISTS,
        object_key="raw/hidden.json",
        storage_class=StorageClass.QUARANTINE,
        detail="replay",
    )
    assert storage_result_to_public_dict(result) == result.to_public_dict()


def test_allowed_storage_write_statuses_vocabulary() -> None:
    assert ALLOWED_STORAGE_WRITE_STATUSES == frozenset(
        {
            "stored",
            "already_exists",
            "conflict",
            "unavailable",
            "rejected",
        }
    )


def test_storage_class_present_in_public_dict() -> None:
    for storage_class in (StorageClass.ACCEPTED, StorageClass.QUARANTINE):
        result = StorageWriteResult(
            status=StorageWriteStatus.UNAVAILABLE,
            storage_class=storage_class,
        )
        assert result.to_public_dict()["storage_class"] == storage_class.value


def test_public_dict_includes_receipt_without_object_key() -> None:
    from codestrata_platform.community_cloud_api.data_lake.immutable_write import (
        build_immutable_raw_storage_object,
    )
    from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy

    envelope = make_envelope()
    storage_object = build_immutable_raw_storage_object(envelope, CommunityDataLakePolicy.default())
    receipt = build_receipt_from_object(StorageWriteStatus.STORED, storage_object)
    result = StorageWriteResult(
        status=StorageWriteStatus.STORED,
        object_key=storage_object.object_key,
        receipt=receipt,
        storage_class=StorageClass.ACCEPTED,
    )
    public = result.to_public_dict()
    assert "object_key" not in public
    assert "receipt" in public
    assert "object_key" not in public["receipt"]
    json.dumps(public, sort_keys=True)

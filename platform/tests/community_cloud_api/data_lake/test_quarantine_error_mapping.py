"""Quarantine error-mapping tests (Slice 8.9)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.canonical_json import CanonicalJsonError
from codestrata_platform.community_cloud_api.data_lake.enums import (
    QuarantineReasonCode,
    QuarantineValidationStage,
)
from codestrata_platform.community_cloud_api.data_lake.errors import (
    DataLakeStorageError,
    StorageErrorCategory,
)
from codestrata_platform.community_cloud_api.data_lake.objects import StorageObjectError
from codestrata_platform.community_cloud_api.data_lake.partitions import PartitionKeyError
from codestrata_platform.community_cloud_api.data_lake.quarantine_error_mapping import (
    map_exception_to_quarantine,
)
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    PartitionProjectionError,
)


def test_storage_object_error_maps_to_invalid_storage_object() -> None:
    mapping = map_exception_to_quarantine(StorageObjectError("bad"))
    assert mapping is not None
    assert mapping.quarantine_reason == QuarantineReasonCode.INVALID_STORAGE_OBJECT.value
    assert mapping.validation_stage == QuarantineValidationStage.STORAGE_OBJECT_VALIDATION.value
    assert "StorageObjectError" not in mapping.to_stable_dict().get("diagnostic_codes", [])


def test_partition_projection_error_maps_to_invalid_partition() -> None:
    mapping = map_exception_to_quarantine(PartitionProjectionError("partition_invalid"))
    assert mapping is not None
    assert mapping.quarantine_reason == QuarantineReasonCode.INVALID_PARTITION.value
    assert mapping.diagnostic_codes == ("partition_invalid",)


def test_checksum_mismatch_maps_correctly() -> None:
    exc = DataLakeStorageError(StorageErrorCategory.CHECKSUM_MISMATCH, "checksum_mismatch")
    mapping = map_exception_to_quarantine(exc)
    assert mapping is not None
    assert mapping.quarantine_reason == QuarantineReasonCode.CHECKSUM_MISMATCH.value
    assert mapping.should_quarantine is True


def test_transient_storage_does_not_quarantine_as_malformed() -> None:
    exc = DataLakeStorageError(StorageErrorCategory.TRANSIENT, "storage_transient")
    mapping = map_exception_to_quarantine(exc)
    assert mapping is not None
    assert mapping.should_quarantine is False


def test_canonical_json_error_maps_to_serialization_failure() -> None:
    mapping = map_exception_to_quarantine(CanonicalJsonError("bad"))
    assert mapping is not None
    assert mapping.quarantine_reason == QuarantineReasonCode.SERIALIZATION_FAILURE.value


def test_partition_key_error_maps_to_storage_key_failure() -> None:
    mapping = map_exception_to_quarantine(PartitionKeyError("bad key"))
    assert mapping is not None
    assert mapping.quarantine_reason == QuarantineReasonCode.STORAGE_KEY_FAILURE.value


def test_mapping_never_embeds_exception_text() -> None:
    mapping = map_exception_to_quarantine(StorageObjectError("secret-token=/Users/alice/leak"))
    assert mapping is not None
    blob = str(mapping.to_stable_dict())
    assert "secret-token" not in blob
    assert "/Users/" not in blob

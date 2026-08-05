"""Production-safe unavailable Community Data Lake store (Slice 8.13).

Implements the full typed storage port and always returns ``UNAVAILABLE``.
No side effects, no local/filesystem/in-memory acceptance, no false STORED.
"""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.community_cloud_api.data_lake.enums import StorageClass, StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.envelopes import DataLakeEnvelope
from codestrata_platform.community_cloud_api.data_lake.objects import ImmutableRawStorageObject
from codestrata_platform.community_cloud_api.data_lake.ports import (
    QuarantineRecord,
    StorageWriteResult,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
    ImmutableQuarantineStorageObject,
)
from codestrata_platform.community_cloud_api.data_lake.storage_capabilities import (
    StorageCapabilities,
)
from codestrata_platform.community_cloud_api.data_lake.storage_configuration import (
    StorageAdapterType,
)
from codestrata_platform.community_cloud_api.data_lake.storage_validation import (
    StorageValidationError,
    assert_accepted_storage_object,
    assert_quarantine_storage_object,
)


@dataclass(frozen=True, slots=True)
class UnavailableCommunityDataLakeStore:
    """Explicit unavailable adapter — production-safe default when unwired."""

    adapter_type: StorageAdapterType = StorageAdapterType.UNAVAILABLE

    @property
    def capabilities(self) -> StorageCapabilities:
        return StorageCapabilities.for_unavailable()

    def put_immutable_storage_object(
        self, storage_object: ImmutableRawStorageObject
    ) -> StorageWriteResult:
        try:
            assert_accepted_storage_object(storage_object)
        except StorageValidationError as exc:
            return StorageWriteResult(
                status=StorageWriteStatus.REJECTED,
                detail=str(exc),
                storage_class=StorageClass.ACCEPTED,
            )
        return StorageWriteResult(
            status=StorageWriteStatus.UNAVAILABLE,
            detail="store_unavailable",
            storage_class=StorageClass.ACCEPTED,
        )

    def put_accepted_object(
        self, storage_object: ImmutableRawStorageObject
    ) -> StorageWriteResult:
        return self.put_immutable_storage_object(storage_object)

    def put_immutable_quarantine_object(
        self, storage_object: ImmutableQuarantineStorageObject
    ) -> StorageWriteResult:
        try:
            assert_quarantine_storage_object(storage_object)
        except StorageValidationError as exc:
            return StorageWriteResult(
                status=StorageWriteStatus.REJECTED,
                detail=str(exc),
                storage_class=StorageClass.QUARANTINE,
            )
        return StorageWriteResult(
            status=StorageWriteStatus.UNAVAILABLE,
            detail="store_unavailable",
            storage_class=StorageClass.QUARANTINE,
        )

    def put_quarantine_object(
        self, storage_object: ImmutableQuarantineStorageObject
    ) -> StorageWriteResult:
        return self.put_immutable_quarantine_object(storage_object)

    def put_immutable_event(self, envelope: DataLakeEnvelope) -> StorageWriteResult:
        return StorageWriteResult(
            status=StorageWriteStatus.UNAVAILABLE,
            detail="store_unavailable",
            storage_class=StorageClass.ACCEPTED,
        )

    def quarantine_event(self, record: QuarantineRecord) -> StorageWriteResult:
        return StorageWriteResult(
            status=StorageWriteStatus.UNAVAILABLE,
            detail="store_unavailable",
            storage_class=StorageClass.QUARANTINE,
        )


__all__ = ["UnavailableCommunityDataLakeStore"]

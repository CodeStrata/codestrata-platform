"""Safe result helpers for Community Data Lake storage writes (Slice 8.13).

Keeps accepted and quarantine receipt types distinct while sharing a
storage-class vocabulary and public serialization that never includes
bucket, key, ARN, ETag, version ID, or AWS request metadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from codestrata_platform.community_cloud_api.data_lake.enums import (
    StorageClass,
    StorageWriteStatus,
)

if TYPE_CHECKING:
    from codestrata_platform.community_cloud_api.data_lake.ports import StorageWriteResult

ALLOWED_STORAGE_WRITE_STATUSES: frozenset[str] = frozenset(
    status.value for status in StorageWriteStatus
)

# Re-export for callers that historically look here for StorageClass.
__all__ = [
    "ALLOWED_STORAGE_WRITE_STATUSES",
    "StorageClass",
    "storage_result_to_public_dict",
]


def storage_result_to_public_dict(result: StorageWriteResult) -> dict[str, Any]:
    """Serialize a write result without ``object_key`` or AWS identifiers."""

    payload: dict[str, Any] = {"status": result.status.value}
    storage_class = getattr(result, "storage_class", None)
    if storage_class is not None:
        value = storage_class.value if isinstance(storage_class, StorageClass) else str(storage_class)
        payload["storage_class"] = value
    if result.detail:
        payload["detail"] = result.detail
    if result.receipt is not None:
        payload["receipt"] = result.receipt.to_public_dict()
    if result.quarantine_receipt is not None:
        payload["quarantine_receipt"] = result.quarantine_receipt.to_public_dict()
    return {key: payload[key] for key in sorted(payload)}

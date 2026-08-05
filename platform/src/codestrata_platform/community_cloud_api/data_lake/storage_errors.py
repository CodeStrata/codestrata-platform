"""Adapter-neutral storage error taxonomy (Slice 8.13).

Reconciles existing :class:`~.errors.StorageErrorCategory` and S3 mapping
safe codes into one documented vocabulary. Does not leak AWS/Python
exception types across the storage port.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.errors import StorageErrorCategory

# Canonical safe_code values used across adapters and diagnostics.
STORAGE_UNAVAILABLE = "storage_unavailable"
STORAGE_TIMEOUT = "storage_timeout"
STORAGE_ACCESS_DENIED = "storage_access_denied"
STORAGE_CONFLICT = "storage_conflict"
STORAGE_CHECKSUM_MISMATCH = "storage_checksum_mismatch"
STORAGE_CONFIGURATION_INVALID = "storage_configuration_invalid"
STORAGE_SERIALIZATION_FAILED = "storage_serialization_failed"
STORAGE_ENCRYPTION_FAILED = "storage_encryption_failed"
STORAGE_REJECTED = "storage_rejected"
STORAGE_INTERNAL_ERROR = "storage_internal_error"
STORAGE_PRECONDITION_FAILED = "storage_precondition_failed"

CANONICAL_STORAGE_SAFE_CODES: frozenset[str] = frozenset(
    {
        STORAGE_UNAVAILABLE,
        STORAGE_TIMEOUT,
        STORAGE_ACCESS_DENIED,
        STORAGE_CONFLICT,
        STORAGE_CHECKSUM_MISMATCH,
        STORAGE_CONFIGURATION_INVALID,
        STORAGE_SERIALIZATION_FAILED,
        STORAGE_ENCRYPTION_FAILED,
        STORAGE_REJECTED,
        STORAGE_INTERNAL_ERROR,
        STORAGE_PRECONDITION_FAILED,
        "storage_unknown_error",
        "store_unavailable",
    }
)

# Map existing category enum values to canonical safe-code families.
CATEGORY_TO_SAFE_CODE_FAMILY: dict[StorageErrorCategory, str] = {
    StorageErrorCategory.ACCESS_DENIED: STORAGE_ACCESS_DENIED,
    StorageErrorCategory.TIMEOUT: STORAGE_TIMEOUT,
    StorageErrorCategory.TRANSIENT: STORAGE_UNAVAILABLE,
    StorageErrorCategory.CHECKSUM_MISMATCH: STORAGE_CHECKSUM_MISMATCH,
    StorageErrorCategory.PRECONDITION: STORAGE_PRECONDITION_FAILED,
    StorageErrorCategory.VALIDATION: STORAGE_REJECTED,
    StorageErrorCategory.NOT_IMPLEMENTED: STORAGE_CONFIGURATION_INVALID,
    StorageErrorCategory.UNKNOWN: STORAGE_INTERNAL_ERROR,
}


__all__ = [
    "CANONICAL_STORAGE_SAFE_CODES",
    "CATEGORY_TO_SAFE_CODE_FAMILY",
    "STORAGE_ACCESS_DENIED",
    "STORAGE_CHECKSUM_MISMATCH",
    "STORAGE_CONFIGURATION_INVALID",
    "STORAGE_CONFLICT",
    "STORAGE_ENCRYPTION_FAILED",
    "STORAGE_INTERNAL_ERROR",
    "STORAGE_PRECONDITION_FAILED",
    "STORAGE_REJECTED",
    "STORAGE_SERIALIZATION_FAILED",
    "STORAGE_TIMEOUT",
    "STORAGE_UNAVAILABLE",
]

"""Bounded diagnostics for Community Data Lake storage abstraction (Slice 8.13).

Never includes bucket names, prefixes, endpoints, credentials, ARNs, object
keys, event IDs, installation IDs, or payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.storage import (
    CommunityDataLakeStoragePolicy,
)
from codestrata_platform.community_cloud_api.data_lake.storage_capabilities import (
    StorageCapabilities,
)
from codestrata_platform.community_cloud_api.data_lake.storage_configuration import (
    StorageAdapterType,
)
from codestrata_platform.community_cloud_api.data_lake.storage_validation import (
    StorageValidationError,
)

ALLOWED_STORAGE_DIAGNOSTIC_STATUSES: frozenset[str] = frozenset({"valid", "invalid"})


@dataclass(frozen=True, slots=True)
class StorageAbstractionDiagnostics:
    """Deterministic, privacy-safe storage-abstraction diagnostics."""

    storage_policy_version: str
    adapter_type: str
    capabilities: tuple[str, ...]
    accepted_write_supported: bool
    quarantine_write_supported: bool
    conditional_create_supported: bool
    retry_verification_supported: bool
    encryption_mode_category: str
    validation_status: str
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.validation_status not in ALLOWED_STORAGE_DIAGNOSTIC_STATUSES:
            raise StorageValidationError(
                "validation_status must be one of "
                f"{sorted(ALLOWED_STORAGE_DIAGNOSTIC_STATUSES)}"
            )
        if not self.storage_policy_version or not self.storage_policy_version.strip():
            raise StorageValidationError("storage_policy_version is required")
        if self.adapter_type not in {item.value for item in StorageAdapterType}:
            raise StorageValidationError("unsupported adapter_type in diagnostics")
        object.__setattr__(self, "capabilities", tuple(sorted(set(self.capabilities))))
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "accepted_write_supported": self.accepted_write_supported,
            "adapter_type": self.adapter_type,
            "capabilities": list(self.capabilities),
            "conditional_create_supported": self.conditional_create_supported,
            "encryption_mode_category": self.encryption_mode_category,
            "limitations": list(self.limitations),
            "quarantine_write_supported": self.quarantine_write_supported,
            "retry_verification_supported": self.retry_verification_supported,
            "storage_policy_version": self.storage_policy_version,
            "validation_status": self.validation_status,
        }
        return {key: payload[key] for key in sorted(payload)}


def diagnostics_from_storage(
    *,
    policy: CommunityDataLakeStoragePolicy,
    adapter_type: StorageAdapterType,
    capabilities: StorageCapabilities,
    encryption_mode_category: str = "sse_s3",
) -> StorageAbstractionDiagnostics:
    """Build diagnostics from validated policy + adapter capability sets."""

    if adapter_type is StorageAdapterType.UNAVAILABLE:
        encryption_mode_category = "none"
    elif adapter_type is StorageAdapterType.IN_MEMORY_TEST:
        encryption_mode_category = "not_applicable_test_adapter"
    return StorageAbstractionDiagnostics(
        storage_policy_version=policy.policy_version,
        adapter_type=adapter_type.value,
        capabilities=tuple(cap.value for cap in capabilities.capabilities),
        accepted_write_supported=capabilities.accepted_write_supported,
        quarantine_write_supported=capabilities.quarantine_write_supported,
        conditional_create_supported=capabilities.conditional_create_supported,
        retry_verification_supported=capabilities.retry_verification_supported,
        encryption_mode_category=encryption_mode_category,
        validation_status="valid",
        limitations=policy.limitations,
    )


__all__ = [
    "ALLOWED_STORAGE_DIAGNOSTIC_STATUSES",
    "StorageAbstractionDiagnostics",
    "diagnostics_from_storage",
]

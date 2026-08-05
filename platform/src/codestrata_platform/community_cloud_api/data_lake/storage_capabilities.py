"""Adapter capability model for Community Data Lake storage (Slice 8.13).

Capabilities describe adapter *behavior* for validation and diagnostics —
they are not IAM resource identifiers and do not authorize security.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.storage_validation import (
    StorageValidationError,
)


class StorageCapability(str, Enum):
    """Bounded storage capabilities an adapter may advertise."""

    ACCEPTED_IMMUTABLE_WRITE = "accepted_immutable_write"
    ACCEPTED_RETRY_VERIFICATION = "accepted_retry_verification"
    QUARANTINE_IMMUTABLE_WRITE = "quarantine_immutable_write"
    QUARANTINE_RETRY_VERIFICATION = "quarantine_retry_verification"
    CONDITIONAL_CREATE = "conditional_create"
    CHECKSUM_VALIDATION = "checksum_validation"
    EXPLICIT_ENCRYPTION = "explicit_encryption"
    UNAVAILABLE = "unavailable"


# Capabilities that must never appear on a Data Lake storage port.
FORBIDDEN_STORAGE_CAPABILITIES: frozenset[str] = frozenset(
    {
        "list",
        "delete",
        "update",
        "copy",
        "move",
        "search",
        "analytics",
        "bucket_admin",
    }
)

_S3_CAPABILITIES: frozenset[StorageCapability] = frozenset(
    {
        StorageCapability.ACCEPTED_IMMUTABLE_WRITE,
        StorageCapability.ACCEPTED_RETRY_VERIFICATION,
        StorageCapability.QUARANTINE_IMMUTABLE_WRITE,
        StorageCapability.QUARANTINE_RETRY_VERIFICATION,
        StorageCapability.CONDITIONAL_CREATE,
        StorageCapability.CHECKSUM_VALIDATION,
        StorageCapability.EXPLICIT_ENCRYPTION,
    }
)

_IN_MEMORY_CAPABILITIES: frozenset[StorageCapability] = frozenset(
    {
        StorageCapability.ACCEPTED_IMMUTABLE_WRITE,
        StorageCapability.ACCEPTED_RETRY_VERIFICATION,
        StorageCapability.QUARANTINE_IMMUTABLE_WRITE,
        StorageCapability.QUARANTINE_RETRY_VERIFICATION,
        StorageCapability.CONDITIONAL_CREATE,
        StorageCapability.CHECKSUM_VALIDATION,
    }
)

_UNAVAILABLE_CAPABILITIES: frozenset[StorageCapability] = frozenset(
    {StorageCapability.UNAVAILABLE}
)


@dataclass(frozen=True, slots=True)
class StorageCapabilities:
    """Immutable capability set for one storage adapter instance."""

    capabilities: frozenset[StorageCapability]

    def __post_init__(self) -> None:
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))
        names = {cap.value for cap in self.capabilities}
        overlap = names & FORBIDDEN_STORAGE_CAPABILITIES
        if overlap:
            raise StorageValidationError(
                f"forbidden storage capabilities: {sorted(overlap)}"
            )
        if (
            StorageCapability.UNAVAILABLE in self.capabilities
            and len(self.capabilities) > 1
        ):
            raise StorageValidationError(
                "unavailable capability cannot combine with write capabilities"
            )

    def supports(self, capability: StorageCapability) -> bool:
        return capability in self.capabilities

    @property
    def accepted_write_supported(self) -> bool:
        return self.supports(StorageCapability.ACCEPTED_IMMUTABLE_WRITE)

    @property
    def quarantine_write_supported(self) -> bool:
        return self.supports(StorageCapability.QUARANTINE_IMMUTABLE_WRITE)

    @property
    def conditional_create_supported(self) -> bool:
        return self.supports(StorageCapability.CONDITIONAL_CREATE)

    @property
    def retry_verification_supported(self) -> bool:
        return self.supports(
            StorageCapability.ACCEPTED_RETRY_VERIFICATION
        ) or self.supports(StorageCapability.QUARANTINE_RETRY_VERIFICATION)

    @property
    def is_unavailable(self) -> bool:
        return self.supports(StorageCapability.UNAVAILABLE)

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "accepted_write_supported": self.accepted_write_supported,
            "capabilities": sorted(cap.value for cap in self.capabilities),
            "conditional_create_supported": self.conditional_create_supported,
            "quarantine_write_supported": self.quarantine_write_supported,
            "retry_verification_supported": self.retry_verification_supported,
            "unavailable": self.is_unavailable,
        }

    @classmethod
    def for_s3(cls) -> StorageCapabilities:
        return cls(_S3_CAPABILITIES)

    @classmethod
    def for_in_memory_test(cls) -> StorageCapabilities:
        return cls(_IN_MEMORY_CAPABILITIES)

    @classmethod
    def for_unavailable(cls) -> StorageCapabilities:
        return cls(_UNAVAILABLE_CAPABILITIES)


__all__ = [
    "FORBIDDEN_STORAGE_CAPABILITIES",
    "StorageCapabilities",
    "StorageCapability",
]

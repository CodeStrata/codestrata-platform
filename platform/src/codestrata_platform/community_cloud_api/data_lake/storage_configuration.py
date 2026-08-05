"""Adapter-mode selection for Community Data Lake storage (Slice 8.13).

Separates mode selection from S3 bucket configuration and from domain
policies. Never reads environment variables. Never embeds credentials,
bucket names, or ARNs in public dumps.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.storage_validation import (
    StorageValidationError,
)


class StorageAdapterType(str, Enum):
    """Explicit adapter modes for the storage factory."""

    UNAVAILABLE = "unavailable"
    IN_MEMORY_TEST = "in_memory_test"
    S3 = "s3"


@dataclass(frozen=True, slots=True)
class DataLakeStorageConfiguration:
    """Validated factory configuration — no ambient env reads.

    ``allow_in_memory_test`` must be set explicitly for the test adapter.
    Production composition must never set it. S3 mode requires a separate
    :class:`~.infrastructure.configuration.S3DataLakeStoreConfiguration`
    passed to the factory (kept off this public dump).
    """

    adapter_type: StorageAdapterType = StorageAdapterType.UNAVAILABLE
    allow_in_memory_test: bool = False
    s3_configuration_provided: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.adapter_type, StorageAdapterType):
            raise StorageValidationError("unsupported storage adapter_type")
        if self.adapter_type is StorageAdapterType.IN_MEMORY_TEST and not self.allow_in_memory_test:
            raise StorageValidationError(
                "in_memory_test requires allow_in_memory_test=True"
            )
        if self.adapter_type is StorageAdapterType.S3 and not self.s3_configuration_provided:
            raise StorageValidationError("s3 adapter requires validated S3 configuration")
        if self.adapter_type is StorageAdapterType.UNAVAILABLE and self.s3_configuration_provided:
            raise StorageValidationError(
                "unavailable adapter must not carry S3 configuration"
            )

    @classmethod
    def unavailable(cls) -> DataLakeStorageConfiguration:
        return cls(adapter_type=StorageAdapterType.UNAVAILABLE)

    @classmethod
    def in_memory_test(cls) -> DataLakeStorageConfiguration:
        return cls(
            adapter_type=StorageAdapterType.IN_MEMORY_TEST,
            allow_in_memory_test=True,
        )

    @classmethod
    def s3(cls) -> DataLakeStorageConfiguration:
        return cls(
            adapter_type=StorageAdapterType.S3,
            s3_configuration_provided=True,
        )

    def to_stable_dict(self) -> dict[str, Any]:
        """Public dump — never includes bucket, prefixes, endpoints, or credentials."""

        return {
            "adapter_type": self.adapter_type.value,
            "allow_in_memory_test": self.allow_in_memory_test,
            "s3_configuration_provided": self.s3_configuration_provided,
        }


__all__ = [
    "DataLakeStorageConfiguration",
    "StorageAdapterType",
]

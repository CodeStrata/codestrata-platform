"""Explicit Community Data Lake storage adapter factory (Slice 8.13).

Production default is ``unavailable``. ``in_memory_test`` requires an
explicit allow flag. ``s3`` requires validated configuration and imports
boto3 lazily only when constructing a real client.

This factory is **not** invoked by ``app.py`` or ``deployment/wiring.py``.
"""

from __future__ import annotations

from typing import Any

from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.ports import (
    CommunityDataLakeStore,
    InMemoryCommunityDataLakeStore,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
    CommunityDataLakeQuarantinePolicy,
    default_quarantine_policy,
)
from codestrata_platform.community_cloud_api.data_lake.storage_configuration import (
    DataLakeStorageConfiguration,
    StorageAdapterType,
)
from codestrata_platform.community_cloud_api.data_lake.storage_validation import (
    StorageValidationError,
)


def create_community_data_lake_store(
    configuration: DataLakeStorageConfiguration | None = None,
    *,
    s3_config: Any | None = None,
    policy: CommunityDataLakePolicy | None = None,
    quarantine_policy: CommunityDataLakeQuarantinePolicy | None = None,
    s3_client: Any | None = None,
) -> CommunityDataLakeStore:
    """Compose a storage adapter from an explicit configuration object.

    Never reads environment variables. Never coerces unknown modes.
    Missing optional boto3 for S3 without an injected client yields a
    configuration failure (or unavailable only when mode is unavailable).
    """

    config = configuration or DataLakeStorageConfiguration.unavailable()
    lake_policy = policy or CommunityDataLakePolicy.default()
    q_policy = quarantine_policy or default_quarantine_policy()

    if config.adapter_type is StorageAdapterType.UNAVAILABLE:
        from codestrata_platform.community_cloud_api.data_lake.infrastructure.unavailable_store import (
            UnavailableCommunityDataLakeStore,
        )

        return UnavailableCommunityDataLakeStore()

    if config.adapter_type is StorageAdapterType.IN_MEMORY_TEST:
        if not config.allow_in_memory_test:
            raise StorageValidationError("in_memory_test requires allow_in_memory_test=True")
        return InMemoryCommunityDataLakeStore(
            policy=lake_policy,
            quarantine_policy=q_policy,
        )

    if config.adapter_type is StorageAdapterType.S3:
        if s3_config is None:
            raise StorageValidationError("s3 adapter requires S3DataLakeStoreConfiguration")
        # Validate S3 config (raises S3ConfigurationError on defect).
        from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
            S3ConfigurationError,
            S3DataLakeStoreConfiguration,
        )
        from codestrata_platform.community_cloud_api.data_lake.infrastructure.s3_store import (
            CommunityDataLakeS3Store,
        )

        if not isinstance(s3_config, S3DataLakeStoreConfiguration):
            raise StorageValidationError("s3_config must be S3DataLakeStoreConfiguration")
        try:
            s3_config.validate()
        except S3ConfigurationError as exc:
            raise StorageValidationError(STORAGE_CONFIGURATION_MESSAGE) from exc

        client = s3_client
        if client is None:
            from codestrata_platform.community_cloud_api.data_lake.infrastructure.client import (
                create_boto3_s3_client,
            )

            try:
                client = create_boto3_s3_client(s3_config)
            except ImportError as exc:
                raise StorageValidationError(
                    "optional_boto3_dependency_missing_for_s3_adapter"
                ) from exc

        return CommunityDataLakeS3Store(
            config=s3_config,
            policy=lake_policy,
            client=client,
            quarantine_policy=q_policy,
        )

    raise StorageValidationError(f"unsupported adapter_type: {config.adapter_type!r}")


STORAGE_CONFIGURATION_MESSAGE = "storage_configuration_invalid"


__all__ = [
    "STORAGE_CONFIGURATION_MESSAGE",
    "create_community_data_lake_store",
]

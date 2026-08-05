"""Storage adapter factory tests (Slice 8.13)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3ConfigurationError,
    S3DataLakeStoreConfiguration,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.unavailable_store import (
    UnavailableCommunityDataLakeStore,
)
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore
from codestrata_platform.community_cloud_api.data_lake.storage_configuration import (
    DataLakeStorageConfiguration,
    StorageAdapterType,
)
from codestrata_platform.community_cloud_api.data_lake.storage_factory import (
    STORAGE_CONFIGURATION_MESSAGE,
    create_community_data_lake_store,
)
from codestrata_platform.community_cloud_api.data_lake.storage_validation import (
    StorageValidationError,
)

from community_cloud_api.data_lake.test_s3_store import FakeS3Client


def test_default_factory_returns_unavailable_store() -> None:
    store = create_community_data_lake_store()
    assert isinstance(store, UnavailableCommunityDataLakeStore)


def test_default_factory_with_none_configuration() -> None:
    store = create_community_data_lake_store(None)
    assert isinstance(store, UnavailableCommunityDataLakeStore)


def test_in_memory_test_factory() -> None:
    store = create_community_data_lake_store(DataLakeStorageConfiguration.in_memory_test())
    assert isinstance(store, InMemoryCommunityDataLakeStore)


def test_cannot_select_in_memory_without_allow_flag() -> None:
    config = SimpleNamespace(
        adapter_type=StorageAdapterType.IN_MEMORY_TEST,
        allow_in_memory_test=False,
    )
    with pytest.raises(StorageValidationError, match="allow_in_memory_test"):
        create_community_data_lake_store(config)  # type: ignore[arg-type]


def test_s3_factory_with_injected_fake_client() -> None:
    client = FakeS3Client()
    s3_config = S3DataLakeStoreConfiguration(bucket_name="valid-bucket-name")
    store = create_community_data_lake_store(
        DataLakeStorageConfiguration.s3(),
        s3_config=s3_config,
        s3_client=client,
    )
    from codestrata_platform.community_cloud_api.data_lake.infrastructure.s3_store import (
        CommunityDataLakeS3Store,
    )

    assert isinstance(store, CommunityDataLakeS3Store)


def test_s3_factory_requires_s3_configuration() -> None:
    with pytest.raises(StorageValidationError, match="S3DataLakeStoreConfiguration"):
        create_community_data_lake_store(DataLakeStorageConfiguration.s3())


def _invalid_s3_config() -> S3DataLakeStoreConfiguration:
    cfg = S3DataLakeStoreConfiguration.__new__(S3DataLakeStoreConfiguration)
    object.__setattr__(cfg, "bucket_name", "INVALID")
    object.__setattr__(cfg, "raw_prefix", "raw/")
    object.__setattr__(cfg, "quarantine_prefix", "quarantine/")
    object.__setattr__(cfg, "encryption_mode", "sse_s3")
    object.__setattr__(cfg, "conditional_write_required", True)
    object.__setattr__(cfg, "checksum_required", True)
    object.__setattr__(cfg, "metadata_digest_key", "codestrata-content-sha256")
    object.__setattr__(cfg, "connect_timeout_seconds", 3.0)
    object.__setattr__(cfg, "read_timeout_seconds", 10.0)
    object.__setattr__(cfg, "max_attempts", 3)
    object.__setattr__(cfg, "endpoint_url", None)
    object.__setattr__(cfg, "policy_version", "1.0")
    object.__setattr__(cfg, "allow_endpoint_override", False)
    return cfg


def test_s3_factory_rejects_invalid_s3_configuration() -> None:
    invalid = _invalid_s3_config()
    with pytest.raises(S3ConfigurationError):
        invalid.validate()
    with pytest.raises(StorageValidationError, match=STORAGE_CONFIGURATION_MESSAGE):
        create_community_data_lake_store(
            DataLakeStorageConfiguration.s3(),
            s3_config=invalid,
            s3_client=FakeS3Client(),
        )


def test_unknown_adapter_type_fails() -> None:
    config = SimpleNamespace(adapter_type="mystery")
    with pytest.raises(StorageValidationError, match="unsupported adapter_type"):
        create_community_data_lake_store(config)  # type: ignore[arg-type]


def test_missing_boto3_raises_storage_validation_error() -> None:
    s3_config = S3DataLakeStoreConfiguration(bucket_name="valid-bucket-name")

    with patch(
        "codestrata_platform.community_cloud_api.data_lake.infrastructure.client.create_boto3_s3_client",
        side_effect=ImportError("no boto3 in test"),
    ):
        with pytest.raises(StorageValidationError, match="optional_boto3_dependency_missing"):
            create_community_data_lake_store(
                DataLakeStorageConfiguration.s3(),
                s3_config=s3_config,
                s3_client=None,
            )

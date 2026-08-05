"""Storage factory configuration boundary tests (Slice 8.13)."""

from __future__ import annotations

from pathlib import Path

import pytest

from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3ConfigurationError,
    S3DataLakeStoreConfiguration,
)
from codestrata_platform.community_cloud_api.data_lake.storage_configuration import (
    DataLakeStorageConfiguration,
    StorageAdapterType,
)
from codestrata_platform.community_cloud_api.data_lake.storage_validation import (
    StorageValidationError,
)


def test_unavailable_mode_is_default() -> None:
    config = DataLakeStorageConfiguration.unavailable()
    assert config.adapter_type is StorageAdapterType.UNAVAILABLE
    assert config.allow_in_memory_test is False
    assert config.s3_configuration_provided is False


def test_in_memory_test_requires_allow_flag() -> None:
    with pytest.raises(StorageValidationError, match="allow_in_memory_test"):
        DataLakeStorageConfiguration(adapter_type=StorageAdapterType.IN_MEMORY_TEST)
    config = DataLakeStorageConfiguration.in_memory_test()
    assert config.allow_in_memory_test is True


def test_s3_requires_s3_configuration_provided() -> None:
    with pytest.raises(StorageValidationError, match="S3 configuration"):
        DataLakeStorageConfiguration(adapter_type=StorageAdapterType.S3)
    config = DataLakeStorageConfiguration.s3()
    assert config.s3_configuration_provided is True


def test_unavailable_must_not_carry_s3_configuration() -> None:
    with pytest.raises(StorageValidationError, match="must not carry S3"):
        DataLakeStorageConfiguration(
            adapter_type=StorageAdapterType.UNAVAILABLE,
            s3_configuration_provided=True,
        )


def test_public_dump_has_no_bucket_or_credentials() -> None:
    blob = DataLakeStorageConfiguration.s3().to_stable_dict()
    assert "bucket" not in blob
    assert "prefix" not in blob
    assert "endpoint" not in blob
    assert "credential" not in blob
    assert blob == {
        "adapter_type": "s3",
        "allow_in_memory_test": False,
        "s3_configuration_provided": True,
    }


@pytest.mark.parametrize(
    "bucket_name,match",
    [
        ("s3://my-bucket", "lowercase"),
        ("my/bucket", "/"),
        ("My-Bucket", "lowercase"),
        ("ab", "3-63"),
    ],
)
def test_s3_configuration_rejects_invalid_bucket_names(bucket_name: str, match: str) -> None:
    with pytest.raises(S3ConfigurationError, match=match):
        S3DataLakeStoreConfiguration(bucket_name=bucket_name)


def test_s3_configuration_rejects_wrong_raw_prefix() -> None:
    with pytest.raises(S3ConfigurationError, match="raw_prefix"):
        S3DataLakeStoreConfiguration(bucket_name="valid-bucket-name", raw_prefix="accepted/")


def test_s3_configuration_rejects_wrong_quarantine_prefix() -> None:
    with pytest.raises(S3ConfigurationError, match="quarantine_prefix"):
        S3DataLakeStoreConfiguration(
            bucket_name="valid-bucket-name", quarantine_prefix="bad/"
        )


def test_s3_configuration_collision_guard_present_in_source() -> None:
    from codestrata_platform.community_cloud_api.data_lake.infrastructure import (
        configuration as config_module,
    )

    source = Path(config_module.__file__).read_text(encoding="utf-8")
    assert "must not collide" in source


def test_s3_configuration_rejects_endpoint_without_allow() -> None:
    with pytest.raises(S3ConfigurationError, match="allow_endpoint_override"):
        S3DataLakeStoreConfiguration(
            bucket_name="valid-bucket-name",
            endpoint_url="http://localhost:4566",
        )


def test_s3_configuration_rejects_non_sse_s3_encryption() -> None:
    with pytest.raises(S3ConfigurationError, match="sse_s3"):
        S3DataLakeStoreConfiguration(
            bucket_name="valid-bucket-name", encryption_mode="sse_kms"
        )

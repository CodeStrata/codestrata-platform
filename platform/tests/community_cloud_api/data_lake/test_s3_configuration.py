"""S3 Data Lake store configuration validation tests (Slice 8.2)."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3ConfigurationError,
    S3DataLakeStoreConfiguration,
)


def test_valid_configuration_constructs_cleanly() -> None:
    config = S3DataLakeStoreConfiguration(bucket_name="codestrata-community-data-lake")
    assert config.raw_prefix == "raw/"
    assert config.encryption_mode == "sse_s3"
    assert config.conditional_write_required is True
    assert config.checksum_required is True


@pytest.mark.parametrize(
    "bucket_name",
    [
        "",
        "ab",  # too short
        "a" * 64,  # too long
        "Has-Uppercase",
        "has_underscore",
        "s3://my-bucket",
        "my/bucket",
        "my:bucket",
        "my.bucket@evil",
        "-leading-hyphen",
        "trailing-hyphen-",
    ],
)
def test_invalid_bucket_names_are_rejected(bucket_name: str) -> None:
    with pytest.raises(S3ConfigurationError):
        S3DataLakeStoreConfiguration(bucket_name=bucket_name)


def test_raw_prefix_must_be_raw_slash() -> None:
    with pytest.raises(S3ConfigurationError):
        S3DataLakeStoreConfiguration(bucket_name="valid-bucket-name", raw_prefix="other/")


def test_only_sse_s3_encryption_is_supported() -> None:
    with pytest.raises(S3ConfigurationError):
        S3DataLakeStoreConfiguration(bucket_name="valid-bucket-name", encryption_mode="sse_kms")


@pytest.mark.parametrize("value", [0.1, 31.0, -1.0])
def test_connect_timeout_bounds_enforced(value: float) -> None:
    with pytest.raises(S3ConfigurationError):
        S3DataLakeStoreConfiguration(bucket_name="valid-bucket-name", connect_timeout_seconds=value)


@pytest.mark.parametrize("value", [0.5, 61.0, -1.0])
def test_read_timeout_bounds_enforced(value: float) -> None:
    with pytest.raises(S3ConfigurationError):
        S3DataLakeStoreConfiguration(bucket_name="valid-bucket-name", read_timeout_seconds=value)


@pytest.mark.parametrize("value", [0, 6, -1])
def test_max_attempts_bounds_enforced(value: int) -> None:
    with pytest.raises(S3ConfigurationError):
        S3DataLakeStoreConfiguration(bucket_name="valid-bucket-name", max_attempts=value)


def test_endpoint_url_requires_allow_endpoint_override() -> None:
    with pytest.raises(S3ConfigurationError):
        S3DataLakeStoreConfiguration(
            bucket_name="valid-bucket-name", endpoint_url="http://localhost:9000"
        )


def test_endpoint_url_permitted_when_override_allowed() -> None:
    config = S3DataLakeStoreConfiguration(
        bucket_name="valid-bucket-name",
        endpoint_url="http://localhost:9000",
        allow_endpoint_override=True,
    )
    assert config.endpoint_url == "http://localhost:9000"


def test_unsupported_policy_version_is_rejected() -> None:
    with pytest.raises(S3ConfigurationError):
        S3DataLakeStoreConfiguration(bucket_name="valid-bucket-name", policy_version="2.0")


def test_configuration_never_reads_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "should-be-ignored")
    monkeypatch.setenv("CODESTRATA_DATA_LAKE_BUCKET", "should-also-be-ignored")
    config = S3DataLakeStoreConfiguration(bucket_name="valid-bucket-name")
    assert config.bucket_name == "valid-bucket-name"

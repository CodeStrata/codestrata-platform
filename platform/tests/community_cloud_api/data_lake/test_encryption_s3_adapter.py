"""S3 adapter encryption behavior (Slice 8.11) — FakeS3, no network."""

from __future__ import annotations

from typing import Any

import pytest

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.errors import StorageErrorCategory
from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3ConfigurationError,
    S3DataLakeStoreConfiguration,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.error_mapping import (
    map_s3_exception,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.s3_store import (
    CommunityDataLakeS3Store,
)
from codestrata_platform.community_cloud_api.data_lake.objects import StorageObjectError
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
    build_quarantine_storage_object,
)

from community_cloud_api.data_lake.test_s3_store import FakeS3Client, _client_error

from ._envelope_test_helpers import make_envelope
from ._quarantine_test_helpers import make_quarantine_record

POLICY = CommunityDataLakePolicy.default()
CONFIG = S3DataLakeStoreConfiguration(bucket_name="codestrata-test-lake-bucket")


def _store(client: FakeS3Client, *, config: S3DataLakeStoreConfiguration = CONFIG) -> CommunityDataLakeS3Store:
    return CommunityDataLakeS3Store(config=config, policy=POLICY, client=client)


def test_accepted_put_sets_aes256_and_no_kms_key() -> None:
    client = FakeS3Client()
    store = _store(client)
    result = store.put_immutable_event(make_envelope(safe_event_reference="evt-encacceptaaaa"))
    assert result.status is StorageWriteStatus.STORED
    _, kwargs = client.calls[0]
    assert kwargs["ServerSideEncryption"] == "AES256"
    assert "SSEKMSKeyId" not in kwargs
    assert "SSECustomerKey" not in kwargs


def test_quarantine_put_sets_aes256_and_no_kms_key() -> None:
    client = FakeS3Client()
    store = _store(client)
    obj = build_quarantine_storage_object(make_quarantine_record())
    result = store.put_immutable_quarantine_object(obj)
    assert result.status is StorageWriteStatus.STORED
    _, kwargs = client.calls[0]
    assert kwargs["ServerSideEncryption"] == "AES256"
    assert "SSEKMSKeyId" not in kwargs
    assert "SSECustomerKey" not in kwargs


def test_accepted_and_quarantine_encryption_headers_match() -> None:
    client = FakeS3Client()
    store = _store(client)
    store.put_immutable_event(make_envelope(safe_event_reference="evt-encparityaaaaaa"))
    store.put_immutable_quarantine_object(build_quarantine_storage_object(make_quarantine_record()))
    accepted_kwargs = next(k for name, k in client.calls if name == "put_object" and k["Key"].startswith("raw/"))
    quarantine_kwargs = next(
        k for name, k in client.calls if name == "put_object" and k["Key"].startswith("quarantine/")
    )
    assert accepted_kwargs["ServerSideEncryption"] == quarantine_kwargs["ServerSideEncryption"] == "AES256"


def test_unsupported_encryption_mode_rejected_before_aws() -> None:
    with pytest.raises(S3ConfigurationError, match="only sse_s3"):
        S3DataLakeStoreConfiguration(bucket_name="codestrata-test-lake-bucket", encryption_mode="sse_kms")
    with pytest.raises(S3ConfigurationError, match="only sse_s3"):
        S3DataLakeStoreConfiguration(bucket_name="codestrata-test-lake-bucket", encryption_mode="none")


def test_store_fail_closed_when_config_mode_mutated_away_from_sse_s3() -> None:
    """Defense in depth: _put_object rejects non-sse_s3 even if config is mutated."""

    client = FakeS3Client()
    config = S3DataLakeStoreConfiguration(bucket_name="codestrata-test-lake-bucket")
    object.__setattr__(config, "encryption_mode", "sse_kms")
    store = _store(client, config=config)
    with pytest.raises(StorageObjectError, match="encryption_mode_unsupported"):
        store._put_object(  # noqa: SLF001 - intentional fail-closed unit probe
            build_quarantine_storage_object(make_quarantine_record())
        )
    assert client.put_object_call_count() == 0


def test_no_unencrypted_fallback_on_retry() -> None:
    def flaky(call_count: int, kwargs: dict[str, Any]) -> Exception | None:
        assert kwargs.get("ServerSideEncryption") == "AES256"
        assert "SSEKMSKeyId" not in kwargs
        if call_count == 1:
            return _client_error("SlowDown")
        return None

    client = FakeS3Client(put_behavior=flaky)
    store = _store(client)
    result = store.put_immutable_event(make_envelope(safe_event_reference="evt-encretryaaaaaaaa"))
    assert result.status is StorageWriteStatus.STORED
    assert client.put_object_call_count() == 2
    for name, kwargs in client.calls:
        if name == "put_object":
            assert kwargs["ServerSideEncryption"] == "AES256"


def test_unexpected_kms_errors_map_to_storage_encryption_failed_not_conflict() -> None:
    class _ClientErrorLike(Exception):
        def __init__(self, code: str) -> None:
            super().__init__(code)
            self.response = {"Error": {"Code": code, "Message": "kms secret detail"}}

    for code in (
        "KMS.NotFoundException",
        "KMS.DisabledException",
        "KMS.AccessDeniedException",
        "KMS.InvalidStateException",
        "KMS.SomethingElse",
    ):
        status, category, safe_code = map_s3_exception(_ClientErrorLike(code))
        assert status is StorageWriteStatus.REJECTED
        assert category is StorageErrorCategory.UNKNOWN
        assert safe_code == "storage_encryption_failed"
        assert "kms secret" not in safe_code


def test_community_data_lake_policy_rejects_sse_kms() -> None:
    from codestrata_platform.community_cloud_api.data_lake.enums import EncryptionMode

    with pytest.raises(ValueError, match="encryption_mode must be sse_s3"):
        CommunityDataLakePolicy(encryption_mode=EncryptionMode.SSE_KMS)

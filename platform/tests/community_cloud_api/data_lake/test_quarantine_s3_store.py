"""S3 quarantine adapter tests (Slice 8.9)."""

from __future__ import annotations

from typing import Any

import pytest

try:
    from botocore.exceptions import ClientError

    _HAS_BOTOCORE = True
except ImportError:  # pragma: no cover
    _HAS_BOTOCORE = False

    class ClientError(Exception):  # type: ignore[no-redef]
        def __init__(self, error_response: dict[str, Any], operation_name: str) -> None:
            super().__init__(operation_name)
            self.response = error_response

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3DataLakeStoreConfiguration,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.s3_store import (
    CommunityDataLakeS3Store,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
    build_quarantine_storage_object,
)

from community_cloud_api.data_lake.test_s3_store import FakeS3Client, _client_error

from ._quarantine_test_helpers import make_quarantine_record

POLICY = CommunityDataLakePolicy.default()
CONFIG = S3DataLakeStoreConfiguration(bucket_name="codestrata-test-lake-bucket")


def _store(client: FakeS3Client) -> CommunityDataLakeS3Store:
    return CommunityDataLakeS3Store(config=CONFIG, policy=POLICY, client=client)


def test_put_immutable_quarantine_object_writes_metadata_allowlist() -> None:
    client = FakeS3Client()
    store = _store(client)
    obj = build_quarantine_storage_object(make_quarantine_record())
    result = store.put_immutable_quarantine_object(obj)
    assert result.status is StorageWriteStatus.STORED
    metadata = client.calls[0][1]["Metadata"]
    assert "codestrata-quarantine-reason" in metadata
    assert "codestrata-stream" not in metadata
    assert client.calls[0][1]["ServerSideEncryption"] == "AES256"


def test_quarantine_conflict_when_digest_differs() -> None:
    client = FakeS3Client()
    store = _store(client)
    first_obj = build_quarantine_storage_object(
        make_quarantine_record(limitations=("alpha",))
    )
    second_obj = build_quarantine_storage_object(
        make_quarantine_record(limitations=("beta",))
    )
    assert first_obj.object_key == second_obj.object_key
    assert first_obj.content_sha256 != second_obj.content_sha256
    first = store.put_immutable_quarantine_object(first_obj)
    second = store.put_immutable_quarantine_object(second_obj)
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.CONFLICT


def test_quarantine_transient_error_retries() -> None:
    def flaky(call_count: int, _kwargs: dict[str, Any]) -> Exception | None:
        if call_count == 1:
            return _client_error("SlowDown")
        return None

    client = FakeS3Client(put_behavior=flaky)
    store = _store(client)
    result = store.quarantine_event(make_quarantine_record())
    assert result.status is StorageWriteStatus.STORED
    assert client.put_object_call_count() == 2


@pytest.mark.skipif(not _HAS_BOTOCORE, reason="botocore required for ClientError shape")
def test_quarantine_access_denied_is_unavailable_or_rejected() -> None:
    def deny(_call_count: int, _kwargs: dict[str, Any]) -> Exception:
        return _client_error("AccessDenied")

    client = FakeS3Client(put_behavior=deny)
    store = _store(client)
    result = store.quarantine_event(make_quarantine_record())
    assert result.status in (StorageWriteStatus.UNAVAILABLE, StorageWriteStatus.REJECTED)
    assert result.detail

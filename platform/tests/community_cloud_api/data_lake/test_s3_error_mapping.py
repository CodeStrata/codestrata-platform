"""S3 exception -> safe outcome mapping tests (Slice 8.2)."""

from __future__ import annotations

from typing import Any

import pytest

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.errors import StorageErrorCategory
from codestrata_platform.community_cloud_api.data_lake.infrastructure.error_mapping import (
    is_transient_storage_error,
    map_s3_exception,
)


class _ClientErrorLike(Exception):
    def __init__(self, code: str, message: str = "synthetic message") -> None:
        super().__init__(message)
        self.response: dict[str, Any] = {"Error": {"Code": code, "Message": message}}


@pytest.mark.parametrize(
    "code,expected_status,expected_category,expected_safe_code",
    [
        ("PreconditionFailed", StorageWriteStatus.CONFLICT, StorageErrorCategory.PRECONDITION, "storage_precondition_failed"),
        ("412", StorageWriteStatus.CONFLICT, StorageErrorCategory.PRECONDITION, "storage_precondition_failed"),
        ("AccessDenied", StorageWriteStatus.REJECTED, StorageErrorCategory.ACCESS_DENIED, "storage_access_denied"),
        ("403", StorageWriteStatus.REJECTED, StorageErrorCategory.ACCESS_DENIED, "storage_access_denied"),
        ("SlowDown", StorageWriteStatus.UNAVAILABLE, StorageErrorCategory.TRANSIENT, "storage_unavailable"),
        ("ServiceUnavailable", StorageWriteStatus.UNAVAILABLE, StorageErrorCategory.TRANSIENT, "storage_unavailable"),
        ("InternalError", StorageWriteStatus.UNAVAILABLE, StorageErrorCategory.TRANSIENT, "storage_unavailable"),
        ("RequestTimeout", StorageWriteStatus.UNAVAILABLE, StorageErrorCategory.TRANSIENT, "storage_unavailable"),
        ("503", StorageWriteStatus.UNAVAILABLE, StorageErrorCategory.TRANSIENT, "storage_unavailable"),
        ("500", StorageWriteStatus.UNAVAILABLE, StorageErrorCategory.TRANSIENT, "storage_unavailable"),
        ("BadDigest", StorageWriteStatus.REJECTED, StorageErrorCategory.CHECKSUM_MISMATCH, "storage_checksum_mismatch"),
        ("InvalidDigest", StorageWriteStatus.REJECTED, StorageErrorCategory.CHECKSUM_MISMATCH, "storage_checksum_mismatch"),
        ("KMS.NotFoundException", StorageWriteStatus.REJECTED, StorageErrorCategory.UNKNOWN, "storage_encryption_failed"),
        ("KMS.DisabledException", StorageWriteStatus.REJECTED, StorageErrorCategory.UNKNOWN, "storage_encryption_failed"),
        ("KMS.AccessDeniedException", StorageWriteStatus.REJECTED, StorageErrorCategory.UNKNOWN, "storage_encryption_failed"),
    ],
)
def test_map_s3_exception_known_codes(
    code: str,
    expected_status: StorageWriteStatus,
    expected_category: StorageErrorCategory,
    expected_safe_code: str,
) -> None:
    status, category, safe_code = map_s3_exception(_ClientErrorLike(code))
    assert status is expected_status
    assert category is expected_category
    assert safe_code == expected_safe_code


def test_map_s3_exception_connect_timeout_by_exception_name() -> None:
    class ConnectTimeoutError(Exception):
        pass

    status, category, safe_code = map_s3_exception(ConnectTimeoutError("no response"))
    assert status is StorageWriteStatus.UNAVAILABLE
    assert category is StorageErrorCategory.TIMEOUT
    assert safe_code == "storage_timeout"


def test_map_s3_exception_read_timeout_by_exception_name() -> None:
    class ReadTimeoutError(Exception):
        pass

    status, category, safe_code = map_s3_exception(ReadTimeoutError("no response"))
    assert status is StorageWriteStatus.UNAVAILABLE
    assert category is StorageErrorCategory.TIMEOUT
    assert safe_code == "storage_timeout"


def test_map_s3_exception_plain_timeout_error() -> None:
    status, category, safe_code = map_s3_exception(TimeoutError("timed out"))
    assert status is StorageWriteStatus.UNAVAILABLE
    assert category is StorageErrorCategory.TIMEOUT


def test_map_s3_exception_unknown_error_is_rejected() -> None:
    status, category, safe_code = map_s3_exception(ValueError("some unrelated failure"))
    assert status is StorageWriteStatus.REJECTED
    assert category is StorageErrorCategory.UNKNOWN
    assert safe_code == "storage_unknown_error"


def test_map_s3_exception_exception_without_response_attribute() -> None:
    status, category, safe_code = map_s3_exception(RuntimeError("boom"))
    assert status is StorageWriteStatus.REJECTED
    assert category is StorageErrorCategory.UNKNOWN


def test_map_s3_exception_never_leaks_raw_message_into_safe_code() -> None:
    secret_message = "bucket=super-secret-bucket key=raw/private/leak.json requestId=ABC123"
    _status, _category, safe_code = map_s3_exception(_ClientErrorLike("AccessDenied", secret_message))
    assert "super-secret-bucket" not in safe_code
    assert "leak.json" not in safe_code
    assert "ABC123" not in safe_code


@pytest.mark.parametrize(
    "category,expected",
    [
        (StorageErrorCategory.TRANSIENT, True),
        (StorageErrorCategory.TIMEOUT, True),
        (StorageErrorCategory.PRECONDITION, False),
        (StorageErrorCategory.ACCESS_DENIED, False),
        (StorageErrorCategory.CHECKSUM_MISMATCH, False),
        (StorageErrorCategory.VALIDATION, False),
        (StorageErrorCategory.NOT_IMPLEMENTED, False),
        (StorageErrorCategory.UNKNOWN, False),
    ],
)
def test_is_transient_storage_error(category: StorageErrorCategory, expected: bool) -> None:
    assert is_transient_storage_error(category) is expected

"""Storage error taxonomy and S3 mapping contract tests (Slice 8.13)."""

from __future__ import annotations

from typing import Any

import pytest

from codestrata_platform.community_cloud_api.data_lake.access_policy import (
    default_access_policy,
)
from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.errors import StorageErrorCategory
from codestrata_platform.community_cloud_api.data_lake.infrastructure.error_mapping import (
    map_s3_exception,
)
from codestrata_platform.community_cloud_api.data_lake.storage_errors import (
    CANONICAL_STORAGE_SAFE_CODES,
    CATEGORY_TO_SAFE_CODE_FAMILY,
    STORAGE_ACCESS_DENIED,
    STORAGE_CHECKSUM_MISMATCH,
    STORAGE_CONFIGURATION_INVALID,
    STORAGE_CONFLICT,
    STORAGE_ENCRYPTION_FAILED,
    STORAGE_INTERNAL_ERROR,
    STORAGE_PRECONDITION_FAILED,
    STORAGE_REJECTED,
    STORAGE_SERIALIZATION_FAILED,
    STORAGE_TIMEOUT,
    STORAGE_UNAVAILABLE,
)


class _ClientErrorLike(Exception):
    def __init__(self, code: str, message: str = "synthetic message") -> None:
        super().__init__(message)
        self.response: dict[str, Any] = {"Error": {"Code": code, "Message": message}}


def test_canonical_storage_safe_codes_include_documented_families() -> None:
    for code in (
        STORAGE_UNAVAILABLE,
        STORAGE_TIMEOUT,
        STORAGE_ACCESS_DENIED,
        STORAGE_CONFLICT,
        STORAGE_CHECKSUM_MISMATCH,
        STORAGE_CONFIGURATION_INVALID,
        STORAGE_SERIALIZATION_FAILED,
        STORAGE_ENCRYPTION_FAILED,
        STORAGE_REJECTED,
        STORAGE_INTERNAL_ERROR,
        STORAGE_PRECONDITION_FAILED,
        "storage_unknown_error",
        "store_unavailable",
    ):
        assert code in CANONICAL_STORAGE_SAFE_CODES


def test_category_to_safe_code_family_covers_all_categories() -> None:
    assert set(CATEGORY_TO_SAFE_CODE_FAMILY) == set(StorageErrorCategory)
    assert CATEGORY_TO_SAFE_CODE_FAMILY[StorageErrorCategory.ACCESS_DENIED] == STORAGE_ACCESS_DENIED
    assert CATEGORY_TO_SAFE_CODE_FAMILY[StorageErrorCategory.VALIDATION] == STORAGE_REJECTED


def test_access_denied_maps_to_rejected_not_stored() -> None:
    status, category, safe_code = map_s3_exception(_ClientErrorLike("AccessDenied"))
    assert status is StorageWriteStatus.REJECTED
    assert category is StorageErrorCategory.ACCESS_DENIED
    assert safe_code == STORAGE_ACCESS_DENIED
    assert status is not StorageWriteStatus.STORED


@pytest.mark.parametrize("code", ["403", "AccessDenied"])
def test_access_denied_codes_never_store(code: str) -> None:
    status, _, safe_code = map_s3_exception(_ClientErrorLike(code))
    assert status is StorageWriteStatus.REJECTED
    assert safe_code == STORAGE_ACCESS_DENIED


def test_precondition_failed_maps_to_conflict_family() -> None:
    status, category, safe_code = map_s3_exception(_ClientErrorLike("PreconditionFailed"))
    assert status is StorageWriteStatus.CONFLICT
    assert category is StorageErrorCategory.PRECONDITION
    assert safe_code == STORAGE_PRECONDITION_FAILED


def test_access_policy_allowed_actions_are_put_and_get_only() -> None:
    policy = default_access_policy()
    assert policy.writer_allowed_actions == frozenset({"s3:PutObject", "s3:GetObject"})
    assert "s3:ListBucket" in policy.writer_forbidden_actions
    assert "s3:DeleteObject" in policy.writer_forbidden_actions

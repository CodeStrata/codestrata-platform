"""Unit tests for encryption validation helpers (Slice 8.11)."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.encryption_validation import (
    EncryptionValidationError,
    assert_no_kms_key_id,
    validate_encryption_mode,
)


def test_validate_encryption_mode_accepts_sse_s3() -> None:
    assert validate_encryption_mode("sse_s3") == "sse_s3"
    assert validate_encryption_mode("  sse_s3  ") == "sse_s3"


def test_validate_encryption_mode_rejects_empty() -> None:
    with pytest.raises(EncryptionValidationError, match="required"):
        validate_encryption_mode("")
    with pytest.raises(EncryptionValidationError, match="required"):
        validate_encryption_mode("   ")


def test_validate_encryption_mode_rejects_sse_kms_operationally() -> None:
    with pytest.raises(EncryptionValidationError, match="only sse_s3"):
        validate_encryption_mode("sse_kms")


def test_validate_encryption_mode_future_documented_still_rejects() -> None:
    with pytest.raises(EncryptionValidationError, match="documented but not operational"):
        validate_encryption_mode("sse_kms", allow_future_documented=True)


def test_validate_encryption_mode_rejects_unknown() -> None:
    with pytest.raises(EncryptionValidationError, match="encryption_mode_unsupported"):
        validate_encryption_mode("none")
    with pytest.raises(EncryptionValidationError, match="encryption_mode_unsupported"):
        validate_encryption_mode("aws:kms")


def test_assert_no_kms_key_id_allows_none_and_blank() -> None:
    assert_no_kms_key_id(None)
    assert_no_kms_key_id("")
    assert_no_kms_key_id("   ")


def test_assert_no_kms_key_id_rejects_any_value() -> None:
    with pytest.raises(EncryptionValidationError, match="kms_key_forbidden"):
        assert_no_kms_key_id("arn:aws:kms:us-east-1:123456789012:key/abc")
    with pytest.raises(EncryptionValidationError, match="kms_key_forbidden"):
        assert_no_kms_key_id("alias/codestrata")

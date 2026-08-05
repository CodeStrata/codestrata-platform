"""Encryption policy diagnostics (Slice 8.11)."""

from __future__ import annotations

import json

import pytest

from codestrata_platform.community_cloud_api.data_lake.encryption_diagnostics import (
    EncryptionPolicyDiagnostics,
    diagnostics_from_encryption_policy,
)
from codestrata_platform.community_cloud_api.data_lake.encryption_policy import (
    default_encryption_policy,
)
from codestrata_platform.community_cloud_api.data_lake.encryption_validation import (
    EncryptionValidationError,
)


def test_diagnostics_from_encryption_policy_shape() -> None:
    policy = default_encryption_policy()
    diag = diagnostics_from_encryption_policy(policy)
    assert isinstance(diag, EncryptionPolicyDiagnostics)
    assert diag.validation_status == "valid"
    assert diag.encryption_policy_version == policy.policy_version
    assert diag.encryption_mode == "sse_s3"
    assert diag.bucket_default_encryption_required is True
    assert diag.explicit_put_encryption_required is True
    assert diag.accepted_prefix_encrypted is True
    assert diag.quarantine_prefix_encrypted is True
    assert diag.kms_enabled is False
    assert diag.key_rotation_required is False
    assert diag.bucket_key_enabled is False
    assert diag.limitations == policy.limitations


def test_diagnostics_have_no_bucket_account_or_key_fields() -> None:
    blob = diagnostics_from_encryption_policy(default_encryption_policy()).to_stable_dict()
    forbidden_keys = {
        "bucket",
        "bucket_name",
        "bucket_arn",
        "account",
        "account_id",
        "arn",
        "object_key",
        "event_id",
        "kms_key_id",
        "key_arn",
        "key_id",
    }
    keys_lower = {str(k).lower() for k in blob}
    assert keys_lower.isdisjoint(forbidden_keys)
    # Policy field names may include "bucket_" (e.g. bucket_key_enabled); values must stay safe.
    serialized = json.dumps(blob, sort_keys=True).lower()
    for token in (
        "arn:",
        "s3://",
        "object_key",
        "event_id",
        "installation_id",
        "kms_key_id",
        "key_arn",
    ):
        assert token not in serialized
    assert blob["kms_enabled"] is False
    assert blob["bucket_key_enabled"] is False


def test_diagnostics_serialization_is_deterministic() -> None:
    diag = diagnostics_from_encryption_policy(default_encryption_policy())
    first = diag.to_stable_dict()
    second = diag.to_stable_dict()
    assert first == second
    assert list(first) == sorted(first)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_invalid_validation_status_rejected() -> None:
    with pytest.raises(EncryptionValidationError, match="validation_status"):
        EncryptionPolicyDiagnostics(
            encryption_policy_version="1.0",
            encryption_mode="sse_s3",
            bucket_default_encryption_required=True,
            explicit_put_encryption_required=True,
            accepted_prefix_encrypted=True,
            quarantine_prefix_encrypted=True,
            kms_enabled=False,
            key_rotation_required=False,
            bucket_key_enabled=False,
            validation_status="maybe",
        )

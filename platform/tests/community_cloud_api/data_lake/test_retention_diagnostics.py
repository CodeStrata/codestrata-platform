"""Retention policy diagnostics (Slice 8.10)."""

from __future__ import annotations

import json

import pytest

from codestrata_platform.community_cloud_api.data_lake.retention_diagnostics import (
    RetentionPolicyDiagnostics,
    diagnostics_from_retention_policy,
)
from codestrata_platform.community_cloud_api.data_lake.retention_policy import (
    default_retention_policy,
)
from codestrata_platform.community_cloud_api.data_lake.retention_validation import (
    RetentionValidationError,
)

_FORBIDDEN_DIAGNOSTIC_TOKENS = (
    "bucket",
    "account",
    "arn:",
    "s3://",
    "object_key",
    "event_id",
    "installation_id",
)


def test_diagnostics_from_retention_policy_shape() -> None:
    policy = default_retention_policy()
    diag = diagnostics_from_retention_policy(policy)
    assert isinstance(diag, RetentionPolicyDiagnostics)
    assert diag.validation_status == "valid"
    assert diag.retention_policy_version == policy.policy_version
    assert diag.accepted_retention_days == 365
    assert diag.quarantine_retention_days == 90
    assert diag.incomplete_multipart_cleanup_days == 7
    assert diag.noncurrent_version_retention_days == 30
    assert diag.versioning_enabled is True
    assert diag.force_destroy_allowed is False
    assert diag.expired_delete_marker_cleanup is True
    assert diag.storage_class_transitions_enabled is False
    assert diag.object_lock_enabled is False
    assert diag.limitations == policy.limitations


def test_diagnostics_have_no_bucket_account_or_key_fields() -> None:
    blob = diagnostics_from_retention_policy(default_retention_policy()).to_stable_dict()
    keys_lower = {str(k).lower() for k in blob}
    for token in ("bucket", "account", "arn", "object_key", "event_id"):
        assert not any(token in key for key in keys_lower), token
    serialized = json.dumps(blob, sort_keys=True).lower()
    for token in _FORBIDDEN_DIAGNOSTIC_TOKENS:
        assert token not in serialized


def test_diagnostics_serialization_is_deterministic() -> None:
    diag = diagnostics_from_retention_policy(default_retention_policy())
    first = diag.to_stable_dict()
    second = diag.to_stable_dict()
    assert first == second
    assert list(first) == sorted(first)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_invalid_validation_status_rejected() -> None:
    with pytest.raises(RetentionValidationError, match="validation_status"):
        RetentionPolicyDiagnostics(
            retention_policy_version="1.0",
            accepted_retention_days=365,
            quarantine_retention_days=90,
            incomplete_multipart_cleanup_days=7,
            noncurrent_version_retention_days=30,
            versioning_enabled=True,
            force_destroy_allowed=False,
            expired_delete_marker_cleanup=True,
            storage_class_transitions_enabled=False,
            object_lock_enabled=False,
            validation_status="maybe",
        )

"""Access policy diagnostics (Slice 8.12)."""

from __future__ import annotations

import json

import pytest

from codestrata_platform.community_cloud_api.data_lake.access_diagnostics import (
    AccessPolicyDiagnostics,
    diagnostics_from_access_policy,
)
from codestrata_platform.community_cloud_api.data_lake.access_policy import (
    default_access_policy,
)
from codestrata_platform.community_cloud_api.data_lake.access_validation import (
    AccessValidationError,
)


def test_diagnostics_from_access_policy_shape() -> None:
    policy = default_access_policy()
    diag = diagnostics_from_access_policy(policy)
    assert isinstance(diag, AccessPolicyDiagnostics)
    assert diag.validation_status == "valid"
    assert diag.access_policy_version == policy.policy_version
    assert diag.writer_accepted_write_allowed is True
    assert diag.writer_accepted_read_allowed is True
    assert diag.writer_quarantine_write_allowed is True
    assert diag.writer_quarantine_read_allowed is True
    assert diag.delete_forbidden is True
    assert diag.bucket_administration_forbidden is True
    assert diag.kms_permissions_required is False
    assert diag.analytics_quarantine_separated is True
    assert diag.writer_attached is False
    assert diag.limitations == policy.limitations


def test_diagnostics_have_no_bucket_account_or_arn_fields() -> None:
    blob = diagnostics_from_access_policy(default_access_policy()).to_stable_dict()
    forbidden_keys = {
        "bucket",
        "bucket_name",
        "bucket_arn",
        "account",
        "account_id",
        "arn",
        "object_key",
        "event_id",
        "writer_policy_arn",
        "writer_policy_name",
        "region",
    }
    keys_lower = {str(k).lower() for k in blob}
    assert keys_lower.isdisjoint(forbidden_keys)
    serialized = json.dumps(blob, sort_keys=True).lower()
    for token in (
        "arn:",
        "s3://",
        "object_key",
        "event_id",
        "installation_id",
        "writer_policy_arn",
    ):
        assert token not in serialized


def test_diagnostics_serialization_is_deterministic() -> None:
    diag = diagnostics_from_access_policy(default_access_policy())
    first = diag.to_stable_dict()
    second = diag.to_stable_dict()
    assert first == second
    assert list(first) == sorted(first)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_invalid_validation_status_rejected() -> None:
    with pytest.raises(AccessValidationError, match="validation_status"):
        AccessPolicyDiagnostics(
            access_policy_version="1.0",
            writer_accepted_write_allowed=True,
            writer_accepted_read_allowed=True,
            writer_quarantine_write_allowed=True,
            writer_quarantine_read_allowed=True,
            delete_forbidden=True,
            bucket_administration_forbidden=True,
            kms_permissions_required=False,
            analytics_quarantine_separated=True,
            writer_attached=False,
            validation_status="maybe",
        )

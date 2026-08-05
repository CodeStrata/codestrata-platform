"""Quarantine policy tests (Slice 8.9)."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.enums import QuarantineReasonCode
from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
    COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_ID,
    COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_URN,
    QUARANTINE_S3_METADATA_ALLOWLIST,
    CommunityDataLakeQuarantinePolicy,
    default_quarantine_policy,
)


def test_default_quarantine_policy_identity() -> None:
    policy = default_quarantine_policy()
    assert policy.policy_id == COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_ID
    assert policy.policy_version == "1.0"
    assert policy.policy_urn == COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_URN
    assert policy.policy_token == COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_URN
    assert policy.retention_days_reference == 90


def test_default_policy_includes_all_reason_codes() -> None:
    policy = default_quarantine_policy()
    for reason in QuarantineReasonCode:
        assert reason.value in policy.allowed_reason_codes


def test_s3_metadata_allowlist_is_quarantine_only() -> None:
    assert QUARANTINE_S3_METADATA_ALLOWLIST == {
        "codestrata-content-sha256",
        "codestrata-quarantine-schema",
        "codestrata-quarantine-reason",
        "codestrata-object-id",
    }
    assert "codestrata-stream" not in QUARANTINE_S3_METADATA_ALLOWLIST
    assert "codestrata-client-type" not in QUARANTINE_S3_METADATA_ALLOWLIST


def test_policy_to_stable_dict_is_sorted() -> None:
    blob = default_quarantine_policy().to_stable_dict()
    assert list(blob) == sorted(blob)


def test_policy_rejects_empty_reason_codes() -> None:
    with pytest.raises(ValueError):
        CommunityDataLakeQuarantinePolicy(allowed_reason_codes=frozenset())

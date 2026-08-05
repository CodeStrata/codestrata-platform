"""Community Data Lake access policy (Slice 8.12)."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace

import pytest

from codestrata_platform.community_cloud_api.data_lake.access_policy import (
    COMMUNITY_DATA_LAKE_ACCESS_POLICY_ID,
    COMMUNITY_DATA_LAKE_ACCESS_POLICY_URN,
    COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION,
    WRITER_ALLOWED_ACTIONS,
    WRITER_FORBIDDEN_ACTIONS,
    CommunityDataLakeAccessPolicy,
    default_access_policy,
)
from codestrata_platform.community_cloud_api.data_lake.access_validation import (
    AccessValidationError,
)


def test_default_access_policy_values() -> None:
    policy = default_access_policy()
    assert policy.policy_id == COMMUNITY_DATA_LAKE_ACCESS_POLICY_ID
    assert policy.policy_version == COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION
    assert policy.policy_token == COMMUNITY_DATA_LAKE_ACCESS_POLICY_URN
    assert policy.writer_allowed_actions == WRITER_ALLOWED_ACTIONS
    assert policy.writer_forbidden_actions == WRITER_FORBIDDEN_ACTIONS
    assert policy.accepted_prefix == "raw/"
    assert policy.quarantine_prefix == "quarantine/"
    assert policy.retry_read_required is True
    assert policy.delete_forbidden is True
    assert policy.list_bucket_allowed is False
    assert policy.bucket_admin_forbidden is True
    assert policy.public_access_admin_forbidden is True
    assert policy.encryption_admin_forbidden is True
    assert policy.lifecycle_admin_forbidden is True
    assert policy.kms_permissions_required is False
    assert policy.analytics_quarantine_separated is True
    assert policy.writer_policy_attached is False
    assert policy.review_status == "writer_policy_unattached_least_privilege_foundation"
    assert "writer_policy_document_unattached" in policy.limitations
    assert "analytics_must_not_auto_include_quarantine" in policy.limitations


def test_default_factory_matches_class_default() -> None:
    assert default_access_policy() == CommunityDataLakeAccessPolicy.default()


def test_policy_urn() -> None:
    assert COMMUNITY_DATA_LAKE_ACCESS_POLICY_URN == "community-data-lake-access-policy:1.0"
    assert default_access_policy().policy_token == COMMUNITY_DATA_LAKE_ACCESS_POLICY_URN


def test_to_stable_dict_is_sorted_and_json_serializable() -> None:
    blob = default_access_policy().to_stable_dict()
    assert list(blob) == sorted(blob)
    text = json.dumps(blob, sort_keys=True)
    assert isinstance(text, str)
    assert blob["accepted_prefix"] == "raw/"
    assert blob["quarantine_prefix"] == "quarantine/"
    assert blob["writer_policy_attached"] is False
    assert blob["list_bucket_allowed"] is False
    assert blob["delete_forbidden"] is True
    assert blob["kms_permissions_required"] is False
    assert blob["analytics_quarantine_separated"] is True
    assert "s3:PutObject" in blob["writer_allowed_actions"]
    assert "s3:GetObject" in blob["writer_allowed_actions"]
    assert "s3:ListBucket" in blob["writer_forbidden_actions"]


def test_rejects_writer_policy_attached_true() -> None:
    with pytest.raises(AccessValidationError, match="writer_policy_attached"):
        CommunityDataLakeAccessPolicy(writer_policy_attached=True)


def test_rejects_list_bucket_allowed_true() -> None:
    with pytest.raises(AccessValidationError, match="list_bucket_allowed"):
        CommunityDataLakeAccessPolicy(list_bucket_allowed=True)


def test_rejects_delete_forbidden_false() -> None:
    with pytest.raises(AccessValidationError, match="delete_forbidden"):
        CommunityDataLakeAccessPolicy(delete_forbidden=False)


def test_rejects_kms_permissions_required_true() -> None:
    with pytest.raises(AccessValidationError, match="kms_permissions_required"):
        CommunityDataLakeAccessPolicy(kms_permissions_required=True)


def test_rejects_analytics_quarantine_separated_false() -> None:
    with pytest.raises(AccessValidationError, match="analytics_quarantine_separated"):
        CommunityDataLakeAccessPolicy(analytics_quarantine_separated=False)


def test_rejects_wrong_prefixes() -> None:
    with pytest.raises(AccessValidationError, match="accepted_prefix"):
        CommunityDataLakeAccessPolicy(accepted_prefix="accepted/")
    with pytest.raises(AccessValidationError, match="quarantine_prefix"):
        CommunityDataLakeAccessPolicy(quarantine_prefix="bad/")


def test_rejects_wrong_policy_id_version_review_status() -> None:
    with pytest.raises(AccessValidationError, match="policy id"):
        CommunityDataLakeAccessPolicy(policy_id="other-policy")
    with pytest.raises(AccessValidationError, match="policy version"):
        CommunityDataLakeAccessPolicy(policy_version="9.9")
    with pytest.raises(AccessValidationError, match="review_status"):
        CommunityDataLakeAccessPolicy(review_status="production_approved")


def test_policy_is_frozen() -> None:
    policy = default_access_policy()
    with pytest.raises(FrozenInstanceError):
        policy.delete_forbidden = False  # type: ignore[misc]


def test_replace_preserves_validation() -> None:
    policy = default_access_policy()
    with pytest.raises(AccessValidationError, match="retry_read_required"):
        replace(policy, retry_read_required=False)

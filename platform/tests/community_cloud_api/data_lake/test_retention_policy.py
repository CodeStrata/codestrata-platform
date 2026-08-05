"""Community Data Lake retention policy (Slice 8.10)."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from codestrata_platform.community_cloud_api.data_lake.retention_policy import (
    ACCEPTED_RETENTION_MAX_DAYS,
    ACCEPTED_RETENTION_MIN_DAYS,
    COMMUNITY_DATA_LAKE_RETENTION_POLICY_ID,
    COMMUNITY_DATA_LAKE_RETENTION_POLICY_URN,
    COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION,
    DEFAULT_ACCEPTED_RETENTION_DAYS,
    DEFAULT_INCOMPLETE_MULTIPART_DAYS,
    DEFAULT_NONCURRENT_VERSION_RETENTION_DAYS,
    DEFAULT_QUARANTINE_RETENTION_DAYS,
    CommunityDataLakeRetentionPolicy,
    default_retention_policy,
)
from codestrata_platform.community_cloud_api.data_lake.retention_validation import (
    RetentionValidationError,
)


def test_default_retention_policy_values() -> None:
    policy = default_retention_policy()
    assert policy.policy_id == COMMUNITY_DATA_LAKE_RETENTION_POLICY_ID
    assert policy.policy_version == COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION
    assert policy.policy_token == COMMUNITY_DATA_LAKE_RETENTION_POLICY_URN
    assert policy.accepted_retention_days == DEFAULT_ACCEPTED_RETENTION_DAYS == 365
    assert policy.quarantine_retention_days == DEFAULT_QUARANTINE_RETENTION_DAYS == 90
    assert policy.incomplete_multipart_cleanup_days == DEFAULT_INCOMPLETE_MULTIPART_DAYS == 7
    assert (
        policy.noncurrent_version_retention_days
        == DEFAULT_NONCURRENT_VERSION_RETENTION_DAYS
        == 30
    )
    assert policy.expired_delete_marker_cleanup is True
    assert policy.versioning_enabled is True
    assert policy.force_destroy_allowed is False
    assert policy.storage_class_transitions_enabled is False
    assert policy.object_lock_enabled is False
    assert policy.review_status == "provisional_requires_release_owner_review"


def test_default_factory_matches_class_default() -> None:
    assert default_retention_policy() == CommunityDataLakeRetentionPolicy.default()


def test_policy_urn() -> None:
    assert (
        COMMUNITY_DATA_LAKE_RETENTION_POLICY_URN
        == "community-data-lake-retention-policy:1.0"
    )
    assert default_retention_policy().policy_token == COMMUNITY_DATA_LAKE_RETENTION_POLICY_URN


def test_to_stable_dict_is_sorted_and_json_serializable() -> None:
    blob = default_retention_policy().to_stable_dict()
    assert list(blob) == sorted(blob)
    text = json.dumps(blob, sort_keys=True)
    assert isinstance(text, str)
    assert blob["policy_token"] == COMMUNITY_DATA_LAKE_RETENTION_POLICY_URN
    assert blob["force_destroy_allowed"] is False
    assert blob["object_lock_enabled"] is False
    assert blob["storage_class_transitions_enabled"] is False


def test_rejects_force_destroy_allowed() -> None:
    with pytest.raises(RetentionValidationError, match="force_destroy_allowed"):
        CommunityDataLakeRetentionPolicy(force_destroy_allowed=True)


def test_rejects_object_lock() -> None:
    with pytest.raises(RetentionValidationError, match="Object Lock"):
        CommunityDataLakeRetentionPolicy(object_lock_enabled=True)


def test_rejects_storage_class_transitions() -> None:
    with pytest.raises(RetentionValidationError, match="storage_class_transitions"):
        CommunityDataLakeRetentionPolicy(storage_class_transitions_enabled=True)


def test_rejects_quarantine_greater_than_accepted() -> None:
    with pytest.raises(RetentionValidationError, match="less than or equal"):
        CommunityDataLakeRetentionPolicy(
            accepted_retention_days=30,
            quarantine_retention_days=90,
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"accepted_retention_days": 0},
        {"accepted_retention_days": -1},
        {"accepted_retention_days": ACCEPTED_RETENTION_MIN_DAYS - 1},
        {"accepted_retention_days": ACCEPTED_RETENTION_MAX_DAYS + 1},
        {"quarantine_retention_days": 0},
        {"quarantine_retention_days": -5},
        {"quarantine_retention_days": 6},
        {"quarantine_retention_days": 366},
        {"incomplete_multipart_cleanup_days": 0},
        {"incomplete_multipart_cleanup_days": 91},
        {"noncurrent_version_retention_days": 0},
        {"noncurrent_version_retention_days": 2556},
        {"versioning_enabled": False},
        {"expired_delete_marker_cleanup": False},
    ],
)
def test_rejects_zero_negative_out_of_bounds_and_required_flags(kwargs: dict) -> None:
    with pytest.raises(RetentionValidationError):
        CommunityDataLakeRetentionPolicy(**kwargs)


def test_policy_is_frozen() -> None:
    policy = default_retention_policy()
    with pytest.raises(FrozenInstanceError):
        policy.accepted_retention_days = 400  # type: ignore[misc]

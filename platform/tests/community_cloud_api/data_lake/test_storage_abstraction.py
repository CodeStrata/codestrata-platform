"""Community Data Lake storage-abstraction policy (Slice 8.13)."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from codestrata_platform.community_cloud_api.data_lake.storage import (
    COMMUNITY_DATA_LAKE_STORAGE_POLICY_ID,
    COMMUNITY_DATA_LAKE_STORAGE_POLICY_URN,
    COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION,
    CommunityDataLakeStoragePolicy,
    default_storage_policy,
)
from codestrata_platform.community_cloud_api.data_lake.storage_validation import (
    StorageValidationError,
)


def test_default_storage_policy_values() -> None:
    policy = default_storage_policy()
    assert policy.policy_id == COMMUNITY_DATA_LAKE_STORAGE_POLICY_ID
    assert policy.policy_version == COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION
    assert policy.policy_token == COMMUNITY_DATA_LAKE_STORAGE_POLICY_URN
    assert policy.projected_object_authority is True
    assert policy.accepted_quarantine_methods_separate is True
    assert policy.envelope_put_authoritative is False
    assert policy.list_allowed is False
    assert policy.delete_allowed is False
    assert policy.update_allowed is False
    assert policy.bucket_admin_allowed is False
    assert policy.production_default_unavailable is True
    assert policy.in_memory_allowed_in_production is False
    assert policy.writer_policy_attached is False
    assert policy.review_status == "projected_object_port_unwired_foundation"
    assert "no_list_delete_update_admin_surface" in policy.limitations
    assert "production_default_adapter_is_unavailable" in policy.limitations
    assert "iam_requires_put_and_get_only" in policy.limitations


def test_default_factory_matches_class_default() -> None:
    assert default_storage_policy() == CommunityDataLakeStoragePolicy.default()


def test_policy_urn() -> None:
    assert COMMUNITY_DATA_LAKE_STORAGE_POLICY_URN == "community-data-lake-storage-policy:1.0"
    assert default_storage_policy().policy_token == COMMUNITY_DATA_LAKE_STORAGE_POLICY_URN


def test_to_stable_dict_is_sorted_and_json_serializable() -> None:
    blob = default_storage_policy().to_stable_dict()
    assert list(blob) == sorted(blob)
    text = json.dumps(blob, sort_keys=True)
    assert isinstance(text, str)
    assert blob["projected_object_authority"] is True
    assert blob["envelope_put_authoritative"] is False
    assert blob["list_allowed"] is False
    assert blob["delete_allowed"] is False
    assert blob["update_allowed"] is False
    assert blob["bucket_admin_allowed"] is False
    assert blob["writer_policy_attached"] is False
    assert blob["production_default_unavailable"] is True
    assert blob["in_memory_allowed_in_production"] is False


def test_rejects_list_allowed_true() -> None:
    with pytest.raises(StorageValidationError, match="list/delete/update"):
        CommunityDataLakeStoragePolicy(list_allowed=True)


def test_rejects_delete_allowed_true() -> None:
    with pytest.raises(StorageValidationError, match="list/delete/update"):
        CommunityDataLakeStoragePolicy(delete_allowed=True)


def test_rejects_update_allowed_true() -> None:
    with pytest.raises(StorageValidationError, match="list/delete/update"):
        CommunityDataLakeStoragePolicy(update_allowed=True)


def test_rejects_bucket_admin_allowed_true() -> None:
    with pytest.raises(StorageValidationError, match="bucket_admin_allowed"):
        CommunityDataLakeStoragePolicy(bucket_admin_allowed=True)


def test_rejects_envelope_put_authoritative_true() -> None:
    with pytest.raises(StorageValidationError, match="envelope_put_authoritative"):
        CommunityDataLakeStoragePolicy(envelope_put_authoritative=True)


def test_rejects_projected_object_authority_false() -> None:
    with pytest.raises(StorageValidationError, match="projected_object_authority"):
        CommunityDataLakeStoragePolicy(projected_object_authority=False)


def test_rejects_accepted_quarantine_methods_separate_false() -> None:
    with pytest.raises(StorageValidationError, match="accepted_quarantine_methods_separate"):
        CommunityDataLakeStoragePolicy(accepted_quarantine_methods_separate=False)


def test_rejects_production_default_unavailable_false() -> None:
    with pytest.raises(StorageValidationError, match="production_default_unavailable"):
        CommunityDataLakeStoragePolicy(production_default_unavailable=False)


def test_rejects_in_memory_allowed_in_production_true() -> None:
    with pytest.raises(StorageValidationError, match="in_memory_allowed_in_production"):
        CommunityDataLakeStoragePolicy(in_memory_allowed_in_production=True)


def test_rejects_writer_policy_attached_true() -> None:
    with pytest.raises(StorageValidationError, match="writer_policy_attached"):
        CommunityDataLakeStoragePolicy(writer_policy_attached=True)


def test_rejects_wrong_policy_id_version_review_status() -> None:
    with pytest.raises(StorageValidationError, match="policy id"):
        CommunityDataLakeStoragePolicy(policy_id="other-policy")
    with pytest.raises(StorageValidationError, match="policy version"):
        CommunityDataLakeStoragePolicy(policy_version="9.9")
    with pytest.raises(StorageValidationError, match="review_status"):
        CommunityDataLakeStoragePolicy(review_status="production_approved")


def test_policy_is_frozen() -> None:
    policy = default_storage_policy()
    with pytest.raises(FrozenInstanceError):
        policy.list_allowed = True  # type: ignore[misc]

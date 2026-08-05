"""Community Data Lake encryption policy (Slice 8.11)."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from codestrata_platform.community_cloud_api.data_lake.encryption_policy import (
    COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_ID,
    COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_URN,
    COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION,
    DEFAULT_ENCRYPTION_MODE,
    SSE_S3_ALGORITHM,
    CommunityDataLakeEncryptionPolicy,
    default_encryption_policy,
)
from codestrata_platform.community_cloud_api.data_lake.encryption_validation import (
    EncryptionValidationError,
)


def test_default_encryption_policy_values() -> None:
    policy = default_encryption_policy()
    assert policy.policy_id == COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_ID
    assert policy.policy_version == COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION
    assert policy.policy_token == COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_URN
    assert policy.encryption_mode == DEFAULT_ENCRYPTION_MODE == "sse_s3"
    assert policy.sse_algorithm == SSE_S3_ALGORITHM == "AES256"
    assert policy.bucket_default_encryption_required is True
    assert policy.explicit_put_encryption_required is True
    assert policy.accepted_prefix_encrypted is True
    assert policy.quarantine_prefix_encrypted is True
    assert policy.kms_key_required is False
    assert policy.kms_key_rotation_required is False
    assert policy.bucket_key_enabled is False
    assert policy.encryption_context_allowed is False
    assert policy.public_key_identifiers_allowed is False
    assert policy.review_status == "sse_s3_foundation_kms_deferred"
    assert "sse_s3_only_in_v0_2_0" in policy.limitations
    assert "no_bucket_policy_deny_unencrypted_writes" in policy.limitations


def test_default_factory_matches_class_default() -> None:
    assert default_encryption_policy() == CommunityDataLakeEncryptionPolicy.default()


def test_policy_urn() -> None:
    assert (
        COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_URN
        == "community-data-lake-encryption-policy:1.0"
    )
    assert default_encryption_policy().policy_token == COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_URN


def test_to_stable_dict_is_sorted_and_json_serializable() -> None:
    blob = default_encryption_policy().to_stable_dict()
    assert list(blob) == sorted(blob)
    text = json.dumps(blob, sort_keys=True)
    assert isinstance(text, str)
    assert blob["encryption_mode"] == "sse_s3"
    assert blob["sse_algorithm"] == "AES256"
    assert blob["bucket_key_enabled"] is False
    assert blob["kms_key_required"] is False
    assert "kms_key_id" not in blob
    assert "key_arn" not in blob


def test_rejects_sse_kms_mode() -> None:
    with pytest.raises(EncryptionValidationError, match="encryption_mode_unsupported"):
        CommunityDataLakeEncryptionPolicy(encryption_mode="sse_kms")


def test_rejects_none_or_arbitrary_mode() -> None:
    with pytest.raises(EncryptionValidationError):
        CommunityDataLakeEncryptionPolicy(encryption_mode="none")
    with pytest.raises(EncryptionValidationError):
        CommunityDataLakeEncryptionPolicy(encryption_mode="client_side")


def test_rejects_bucket_key_enabled() -> None:
    with pytest.raises(EncryptionValidationError, match="bucket_key_enabled"):
        CommunityDataLakeEncryptionPolicy(bucket_key_enabled=True)


def test_rejects_kms_required_flags() -> None:
    with pytest.raises(EncryptionValidationError, match="KMS"):
        CommunityDataLakeEncryptionPolicy(kms_key_required=True)
    with pytest.raises(EncryptionValidationError, match="KMS"):
        CommunityDataLakeEncryptionPolicy(kms_key_rotation_required=True)


def test_rejects_non_aes256_algorithm() -> None:
    with pytest.raises(EncryptionValidationError, match="AES256"):
        CommunityDataLakeEncryptionPolicy(sse_algorithm="aws:kms")


def test_rejects_disabled_bucket_or_put_requirements() -> None:
    with pytest.raises(EncryptionValidationError, match="bucket_default_encryption"):
        CommunityDataLakeEncryptionPolicy(bucket_default_encryption_required=False)
    with pytest.raises(EncryptionValidationError, match="explicit_put_encryption"):
        CommunityDataLakeEncryptionPolicy(explicit_put_encryption_required=False)


def test_rejects_prefix_parity_gap() -> None:
    with pytest.raises(EncryptionValidationError, match="accepted and quarantine"):
        CommunityDataLakeEncryptionPolicy(accepted_prefix_encrypted=False)
    with pytest.raises(EncryptionValidationError, match="accepted and quarantine"):
        CommunityDataLakeEncryptionPolicy(quarantine_prefix_encrypted=False)


def test_rejects_encryption_context_and_public_key_ids() -> None:
    with pytest.raises(EncryptionValidationError, match="encryption_context"):
        CommunityDataLakeEncryptionPolicy(encryption_context_allowed=True)
    with pytest.raises(EncryptionValidationError, match="public key identifiers"):
        CommunityDataLakeEncryptionPolicy(public_key_identifiers_allowed=True)


def test_rejects_wrong_policy_id_version_review_status() -> None:
    with pytest.raises(EncryptionValidationError, match="policy id"):
        CommunityDataLakeEncryptionPolicy(policy_id="other-policy")
    with pytest.raises(EncryptionValidationError, match="policy version"):
        CommunityDataLakeEncryptionPolicy(policy_version="9.9")
    with pytest.raises(EncryptionValidationError, match="review_status"):
        CommunityDataLakeEncryptionPolicy(review_status="production_approved")


def test_policy_is_frozen() -> None:
    policy = default_encryption_policy()
    with pytest.raises(FrozenInstanceError):
        policy.encryption_mode = "sse_kms"  # type: ignore[misc]

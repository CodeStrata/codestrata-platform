"""Independent Community Data Lake encryption-at-rest policy (Slice 8.11).

:class:`CommunityDataLakeEncryptionPolicy` is the Platform-side product-policy
contract for encryption *defaults*. It reconciles with
``infrastructure/modules/community-data-lake/encryption.tf`` and the S3
adapter's ``ServerSideEncryption=AES256`` PutObject behavior through static
tests — it does **not** import or override HCL at runtime.

v0.2.0 decision: **SSE-S3 (AES256)** only. Customer-managed KMS is a
documented future migration, not an enabled alternative.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.enums import EncryptionMode
from codestrata_platform.community_cloud_api.data_lake.encryption_validation import (
    EncryptionValidationError,
    validate_encryption_mode,
)

COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_ID = "community-data-lake-encryption-policy"
COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION = "1.0"
COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_URN = (
    f"{COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_ID}:"
    f"{COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION}"
)

DEFAULT_ENCRYPTION_MODE = EncryptionMode.SSE_S3.value
SSE_S3_ALGORITHM = "AES256"

_REVIEW_STATUS = "sse_s3_foundation_kms_deferred"

_LIMITATIONS: tuple[str, ...] = (
    "sse_s3_only_in_v0_2_0",
    "kms_deferred_not_operational",
    "no_customer_managed_key",
    "no_bucket_policy_deny_unencrypted_writes",
    "bucket_default_plus_explicit_put_headers",
    "in_memory_store_does_not_cryptographically_encrypt",
    "platform_references_infrastructure_does_not_override_hcl",
    "no_endpoint_or_app_wiring",
    "no_key_identifiers_in_product_contracts",
)


@dataclass(frozen=True, slots=True)
class CommunityDataLakeEncryptionPolicy:
    """Deterministic, versioned encryption-at-rest product-policy contract."""

    policy_id: str = COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_ID
    policy_version: str = COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION
    encryption_mode: str = DEFAULT_ENCRYPTION_MODE
    bucket_default_encryption_required: bool = True
    explicit_put_encryption_required: bool = True
    accepted_prefix_encrypted: bool = True
    quarantine_prefix_encrypted: bool = True
    kms_key_required: bool = False
    kms_key_rotation_required: bool = False
    bucket_key_enabled: bool = False
    encryption_context_allowed: bool = False
    public_key_identifiers_allowed: bool = False
    sse_algorithm: str = SSE_S3_ALGORITHM
    review_status: str = _REVIEW_STATUS
    limitations: tuple[str, ...] = _LIMITATIONS

    def __post_init__(self) -> None:
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))
        self.validate()

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    def validate(self) -> None:
        if self.policy_id != COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_ID:
            raise EncryptionValidationError("unsupported encryption policy id")
        if self.policy_version != COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION:
            raise EncryptionValidationError("unsupported encryption policy version")
        if self.review_status != _REVIEW_STATUS:
            raise EncryptionValidationError("unsupported encryption review_status")
        validate_encryption_mode(self.encryption_mode)
        if self.sse_algorithm != SSE_S3_ALGORITHM:
            raise EncryptionValidationError("sse_algorithm must be AES256 for sse_s3")
        if not self.bucket_default_encryption_required:
            raise EncryptionValidationError("bucket_default_encryption_required must be true")
        if not self.explicit_put_encryption_required:
            raise EncryptionValidationError("explicit_put_encryption_required must be true")
        if not self.accepted_prefix_encrypted or not self.quarantine_prefix_encrypted:
            raise EncryptionValidationError(
                "accepted and quarantine prefixes must both require encryption"
            )
        if self.kms_key_required or self.kms_key_rotation_required:
            raise EncryptionValidationError("KMS is not operational in v0.2.0")
        if self.bucket_key_enabled:
            raise EncryptionValidationError(
                "bucket_key_enabled must be false under sse_s3 (S3 Bucket Keys are SSE-KMS)"
            )
        if self.encryption_context_allowed:
            raise EncryptionValidationError("encryption_context is not allowed under sse_s3")
        if self.public_key_identifiers_allowed:
            raise EncryptionValidationError("public key identifiers are never allowed")

    @classmethod
    def default(cls) -> CommunityDataLakeEncryptionPolicy:
        return cls()

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "accepted_prefix_encrypted": self.accepted_prefix_encrypted,
            "bucket_default_encryption_required": self.bucket_default_encryption_required,
            "bucket_key_enabled": self.bucket_key_enabled,
            "encryption_context_allowed": self.encryption_context_allowed,
            "encryption_mode": self.encryption_mode,
            "explicit_put_encryption_required": self.explicit_put_encryption_required,
            "kms_key_required": self.kms_key_required,
            "kms_key_rotation_required": self.kms_key_rotation_required,
            "limitations": list(self.limitations),
            "policy_id": self.policy_id,
            "policy_token": self.policy_token,
            "policy_version": self.policy_version,
            "public_key_identifiers_allowed": self.public_key_identifiers_allowed,
            "quarantine_prefix_encrypted": self.quarantine_prefix_encrypted,
            "review_status": self.review_status,
            "sse_algorithm": self.sse_algorithm,
        }


def default_encryption_policy() -> CommunityDataLakeEncryptionPolicy:
    return CommunityDataLakeEncryptionPolicy.default()


__all__ = [
    "COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_ID",
    "COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_URN",
    "COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION",
    "CommunityDataLakeEncryptionPolicy",
    "DEFAULT_ENCRYPTION_MODE",
    "SSE_S3_ALGORITHM",
    "default_encryption_policy",
]

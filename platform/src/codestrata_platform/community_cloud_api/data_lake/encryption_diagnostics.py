"""Bounded diagnostics for Community Data Lake encryption policy (Slice 8.11).

Never includes bucket names, ARNs, key IDs, account IDs, regions, object keys,
or event identities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.encryption_policy import (
    CommunityDataLakeEncryptionPolicy,
)
from codestrata_platform.community_cloud_api.data_lake.encryption_validation import (
    EncryptionValidationError,
)

ALLOWED_ENCRYPTION_DIAGNOSTIC_STATUSES: frozenset[str] = frozenset({"valid", "invalid"})


@dataclass(frozen=True, slots=True)
class EncryptionPolicyDiagnostics:
    """Deterministic, privacy-safe encryption policy diagnostics."""

    encryption_policy_version: str
    encryption_mode: str
    bucket_default_encryption_required: bool
    explicit_put_encryption_required: bool
    accepted_prefix_encrypted: bool
    quarantine_prefix_encrypted: bool
    kms_enabled: bool
    key_rotation_required: bool
    bucket_key_enabled: bool
    validation_status: str
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.validation_status not in ALLOWED_ENCRYPTION_DIAGNOSTIC_STATUSES:
            raise EncryptionValidationError(
                "validation_status must be one of "
                f"{sorted(ALLOWED_ENCRYPTION_DIAGNOSTIC_STATUSES)}"
            )
        if not self.encryption_policy_version or not self.encryption_policy_version.strip():
            raise EncryptionValidationError("encryption_policy_version is required")
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "accepted_prefix_encrypted": self.accepted_prefix_encrypted,
            "bucket_default_encryption_required": self.bucket_default_encryption_required,
            "bucket_key_enabled": self.bucket_key_enabled,
            "encryption_mode": self.encryption_mode,
            "encryption_policy_version": self.encryption_policy_version,
            "explicit_put_encryption_required": self.explicit_put_encryption_required,
            "key_rotation_required": self.key_rotation_required,
            "kms_enabled": self.kms_enabled,
            "limitations": list(self.limitations),
            "quarantine_prefix_encrypted": self.quarantine_prefix_encrypted,
            "validation_status": self.validation_status,
        }
        return {key: payload[key] for key in sorted(payload)}


def diagnostics_from_encryption_policy(
    policy: CommunityDataLakeEncryptionPolicy,
) -> EncryptionPolicyDiagnostics:
    """Build diagnostics from a validated encryption policy (always ``valid``)."""

    return EncryptionPolicyDiagnostics(
        encryption_policy_version=policy.policy_version,
        encryption_mode=policy.encryption_mode,
        bucket_default_encryption_required=policy.bucket_default_encryption_required,
        explicit_put_encryption_required=policy.explicit_put_encryption_required,
        accepted_prefix_encrypted=policy.accepted_prefix_encrypted,
        quarantine_prefix_encrypted=policy.quarantine_prefix_encrypted,
        kms_enabled=policy.kms_key_required,
        key_rotation_required=policy.kms_key_rotation_required,
        bucket_key_enabled=policy.bucket_key_enabled,
        validation_status="valid",
        limitations=policy.limitations,
    )


__all__ = [
    "ALLOWED_ENCRYPTION_DIAGNOSTIC_STATUSES",
    "EncryptionPolicyDiagnostics",
    "diagnostics_from_encryption_policy",
]

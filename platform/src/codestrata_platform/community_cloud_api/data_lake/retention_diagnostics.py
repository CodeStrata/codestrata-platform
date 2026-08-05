"""Bounded diagnostics for Community Data Lake retention policy (Slice 8.10).

These values are infrastructure / product-policy numbers — never customer
data, bucket ARNs, account IDs, object keys, or event identities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.retention_policy import (
    CommunityDataLakeRetentionPolicy,
)
from codestrata_platform.community_cloud_api.data_lake.retention_validation import (
    RetentionValidationError,
)

ALLOWED_RETENTION_DIAGNOSTIC_STATUSES: frozenset[str] = frozenset({"valid", "invalid"})


@dataclass(frozen=True, slots=True)
class RetentionPolicyDiagnostics:
    """Deterministic, privacy-safe retention policy diagnostics."""

    retention_policy_version: str
    accepted_retention_days: int
    quarantine_retention_days: int
    incomplete_multipart_cleanup_days: int
    noncurrent_version_retention_days: int
    versioning_enabled: bool
    force_destroy_allowed: bool
    expired_delete_marker_cleanup: bool
    storage_class_transitions_enabled: bool
    object_lock_enabled: bool
    validation_status: str
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.validation_status not in ALLOWED_RETENTION_DIAGNOSTIC_STATUSES:
            raise RetentionValidationError(
                f"validation_status must be one of {sorted(ALLOWED_RETENTION_DIAGNOSTIC_STATUSES)}"
            )
        if not self.retention_policy_version or not self.retention_policy_version.strip():
            raise RetentionValidationError("retention_policy_version is required")
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "accepted_retention_days": self.accepted_retention_days,
            "expired_delete_marker_cleanup": self.expired_delete_marker_cleanup,
            "force_destroy_allowed": self.force_destroy_allowed,
            "incomplete_multipart_cleanup_days": self.incomplete_multipart_cleanup_days,
            "limitations": list(self.limitations),
            "noncurrent_version_retention_days": self.noncurrent_version_retention_days,
            "object_lock_enabled": self.object_lock_enabled,
            "quarantine_retention_days": self.quarantine_retention_days,
            "retention_policy_version": self.retention_policy_version,
            "storage_class_transitions_enabled": self.storage_class_transitions_enabled,
            "validation_status": self.validation_status,
            "versioning_enabled": self.versioning_enabled,
        }
        return {key: payload[key] for key in sorted(payload)}


def diagnostics_from_retention_policy(
    policy: CommunityDataLakeRetentionPolicy,
) -> RetentionPolicyDiagnostics:
    """Build diagnostics from a validated retention policy (always ``valid``)."""

    return RetentionPolicyDiagnostics(
        retention_policy_version=policy.policy_version,
        accepted_retention_days=policy.accepted_retention_days,
        quarantine_retention_days=policy.quarantine_retention_days,
        incomplete_multipart_cleanup_days=policy.incomplete_multipart_cleanup_days,
        noncurrent_version_retention_days=policy.noncurrent_version_retention_days,
        versioning_enabled=policy.versioning_enabled,
        force_destroy_allowed=policy.force_destroy_allowed,
        expired_delete_marker_cleanup=policy.expired_delete_marker_cleanup,
        storage_class_transitions_enabled=policy.storage_class_transitions_enabled,
        object_lock_enabled=policy.object_lock_enabled,
        validation_status="valid",
        limitations=policy.limitations,
    )


__all__ = [
    "ALLOWED_RETENTION_DIAGNOSTIC_STATUSES",
    "RetentionPolicyDiagnostics",
    "diagnostics_from_retention_policy",
]

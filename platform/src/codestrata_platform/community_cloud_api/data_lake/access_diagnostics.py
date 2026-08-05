"""Bounded diagnostics for Community Data Lake access policy (Slice 8.12).

Never includes bucket names, ARNs, account IDs, regions, object keys, or
event identities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.access_policy import (
    CommunityDataLakeAccessPolicy,
)
from codestrata_platform.community_cloud_api.data_lake.access_validation import (
    AccessValidationError,
)

ALLOWED_ACCESS_DIAGNOSTIC_STATUSES: frozenset[str] = frozenset({"valid", "invalid"})


@dataclass(frozen=True, slots=True)
class AccessPolicyDiagnostics:
    """Deterministic, privacy-safe access-policy diagnostics."""

    access_policy_version: str
    writer_accepted_write_allowed: bool
    writer_accepted_read_allowed: bool
    writer_quarantine_write_allowed: bool
    writer_quarantine_read_allowed: bool
    delete_forbidden: bool
    bucket_administration_forbidden: bool
    kms_permissions_required: bool
    analytics_quarantine_separated: bool
    writer_attached: bool
    validation_status: str
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.validation_status not in ALLOWED_ACCESS_DIAGNOSTIC_STATUSES:
            raise AccessValidationError(
                "validation_status must be one of "
                f"{sorted(ALLOWED_ACCESS_DIAGNOSTIC_STATUSES)}"
            )
        if not self.access_policy_version or not self.access_policy_version.strip():
            raise AccessValidationError("access_policy_version is required")
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "access_policy_version": self.access_policy_version,
            "analytics_quarantine_separated": self.analytics_quarantine_separated,
            "bucket_administration_forbidden": self.bucket_administration_forbidden,
            "delete_forbidden": self.delete_forbidden,
            "kms_permissions_required": self.kms_permissions_required,
            "limitations": list(self.limitations),
            "validation_status": self.validation_status,
            "writer_accepted_read_allowed": self.writer_accepted_read_allowed,
            "writer_accepted_write_allowed": self.writer_accepted_write_allowed,
            "writer_attached": self.writer_attached,
            "writer_quarantine_read_allowed": self.writer_quarantine_read_allowed,
            "writer_quarantine_write_allowed": self.writer_quarantine_write_allowed,
        }
        return {key: payload[key] for key in sorted(payload)}


def diagnostics_from_access_policy(
    policy: CommunityDataLakeAccessPolicy,
) -> AccessPolicyDiagnostics:
    """Build diagnostics from a validated access policy (always ``valid``)."""

    put = "s3:PutObject" in policy.writer_allowed_actions
    get = "s3:GetObject" in policy.writer_allowed_actions
    return AccessPolicyDiagnostics(
        access_policy_version=policy.policy_version,
        writer_accepted_write_allowed=put,
        writer_accepted_read_allowed=get and policy.retry_read_required,
        writer_quarantine_write_allowed=put,
        writer_quarantine_read_allowed=get and policy.retry_read_required,
        delete_forbidden=policy.delete_forbidden,
        bucket_administration_forbidden=policy.bucket_admin_forbidden,
        kms_permissions_required=policy.kms_permissions_required,
        analytics_quarantine_separated=policy.analytics_quarantine_separated,
        writer_attached=policy.writer_policy_attached,
        validation_status="valid",
        limitations=policy.limitations,
    )


__all__ = [
    "ALLOWED_ACCESS_DIAGNOSTIC_STATUSES",
    "AccessPolicyDiagnostics",
    "diagnostics_from_access_policy",
]

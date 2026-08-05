"""Independent Community Data Lake retention policy (Slice 8.10).

:class:`CommunityDataLakeRetentionPolicy` is the Platform-side product-policy
contract for retention and lifecycle *defaults*. It references the same
numeric defaults and bounds as
``infrastructure/modules/community-data-lake`` OpenTofu variables, but does
**not** import or override HCL at runtime. Reconciliation is enforced by
static tests that compare both layers.

This policy is independent from:

- :class:`~.policy.CommunityDataLakePolicy` (storage/envelope policy 1.0)
- :class:`~.quarantine_policy.CommunityDataLakeQuarantinePolicy` (quarantine 1.0)
- stream partition policies
- Community Cloud API version

Defaults are **provisional product-policy starting points** requiring
release-owner review before production deployment. They are not a claim of
legal or multi-jurisdiction privacy compliance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.retention_validation import (
    RetentionValidationError,
    validate_retention_values,
)

COMMUNITY_DATA_LAKE_RETENTION_POLICY_ID = "community-data-lake-retention-policy"
COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION = "1.0"
COMMUNITY_DATA_LAKE_RETENTION_POLICY_URN = (
    f"{COMMUNITY_DATA_LAKE_RETENTION_POLICY_ID}:"
    f"{COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION}"
)

# Product-policy defaults — must stay aligned with infrastructure module
# variable defaults (see platform/tests reconciliation).
DEFAULT_ACCEPTED_RETENTION_DAYS = 365
DEFAULT_QUARANTINE_RETENTION_DAYS = 90
DEFAULT_INCOMPLETE_MULTIPART_DAYS = 7
DEFAULT_NONCURRENT_VERSION_RETENTION_DAYS = 30

# Bounds — must stay aligned with infrastructure variable validation blocks.
ACCEPTED_RETENTION_MIN_DAYS = 30
ACCEPTED_RETENTION_MAX_DAYS = 2555
QUARANTINE_RETENTION_MIN_DAYS = 7
QUARANTINE_RETENTION_MAX_DAYS = 365
INCOMPLETE_MULTIPART_MIN_DAYS = 1
INCOMPLETE_MULTIPART_MAX_DAYS = 90
NONCURRENT_VERSION_MIN_DAYS = 1
NONCURRENT_VERSION_MAX_DAYS = 2555

_REVIEW_STATUS_PROVISIONAL = "provisional_requires_release_owner_review"

_LIMITATIONS: tuple[str, ...] = (
    "provisional_defaults_require_release_owner_review",
    "not_a_legal_or_jurisdictional_compliance_claim",
    "platform_references_infrastructure_does_not_override_hcl",
    "no_per_stream_retention_overrides_in_v0_2_0",
    "no_storage_class_transitions",
    "no_s3_object_lock",
    "no_application_deletion_or_opt_out_api",
    "lifecycle_expiry_not_equivalent_to_privacy_erasure",
    "durable_identity_retention_coordination_deferred",
    "no_endpoint_or_app_wiring",
)


@dataclass(frozen=True, slots=True)
class CommunityDataLakeRetentionPolicy:
    """Deterministic, versioned retention / lifecycle product-policy contract."""

    policy_id: str = COMMUNITY_DATA_LAKE_RETENTION_POLICY_ID
    policy_version: str = COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION
    accepted_retention_days: int = DEFAULT_ACCEPTED_RETENTION_DAYS
    quarantine_retention_days: int = DEFAULT_QUARANTINE_RETENTION_DAYS
    incomplete_multipart_cleanup_days: int = DEFAULT_INCOMPLETE_MULTIPART_DAYS
    noncurrent_version_retention_days: int = DEFAULT_NONCURRENT_VERSION_RETENTION_DAYS
    expired_delete_marker_cleanup: bool = True
    versioning_enabled: bool = True
    force_destroy_allowed: bool = False
    storage_class_transitions_enabled: bool = False
    object_lock_enabled: bool = False
    review_status: str = _REVIEW_STATUS_PROVISIONAL
    accepted_retention_min_days: int = ACCEPTED_RETENTION_MIN_DAYS
    accepted_retention_max_days: int = ACCEPTED_RETENTION_MAX_DAYS
    quarantine_retention_min_days: int = QUARANTINE_RETENTION_MIN_DAYS
    quarantine_retention_max_days: int = QUARANTINE_RETENTION_MAX_DAYS
    incomplete_multipart_min_days: int = INCOMPLETE_MULTIPART_MIN_DAYS
    incomplete_multipart_max_days: int = INCOMPLETE_MULTIPART_MAX_DAYS
    noncurrent_version_min_days: int = NONCURRENT_VERSION_MIN_DAYS
    noncurrent_version_max_days: int = NONCURRENT_VERSION_MAX_DAYS
    limitations: tuple[str, ...] = _LIMITATIONS

    def __post_init__(self) -> None:
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))
        self.validate()

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    def validate(self) -> None:
        if self.policy_id != COMMUNITY_DATA_LAKE_RETENTION_POLICY_ID:
            raise RetentionValidationError("unsupported retention policy id")
        if self.policy_version != COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION:
            raise RetentionValidationError("unsupported retention policy version")
        if self.review_status != _REVIEW_STATUS_PROVISIONAL:
            raise RetentionValidationError("unsupported retention review_status")
        if self.force_destroy_allowed:
            raise RetentionValidationError(
                "force_destroy_allowed must be false for the product-policy default"
            )
        if self.storage_class_transitions_enabled:
            raise RetentionValidationError(
                "storage_class_transitions are not approved for v0.2.0"
            )
        if self.object_lock_enabled:
            raise RetentionValidationError("S3 Object Lock is not approved for v0.2.0")
        if not self.versioning_enabled:
            raise RetentionValidationError(
                "versioning_enabled must be true (explicit Enabled posture)"
            )
        if not self.expired_delete_marker_cleanup:
            raise RetentionValidationError(
                "expired_delete_marker_cleanup must be true "
                "(prevents indefinite delete-marker retention)"
            )
        validate_retention_values(
            accepted_retention_days=self.accepted_retention_days,
            quarantine_retention_days=self.quarantine_retention_days,
            incomplete_multipart_cleanup_days=self.incomplete_multipart_cleanup_days,
            noncurrent_version_retention_days=self.noncurrent_version_retention_days,
            accepted_min=self.accepted_retention_min_days,
            accepted_max=self.accepted_retention_max_days,
            quarantine_min=self.quarantine_retention_min_days,
            quarantine_max=self.quarantine_retention_max_days,
            multipart_min=self.incomplete_multipart_min_days,
            multipart_max=self.incomplete_multipart_max_days,
            noncurrent_min=self.noncurrent_version_min_days,
            noncurrent_max=self.noncurrent_version_max_days,
            require_quarantine_le_accepted=True,
        )

    @classmethod
    def default(cls) -> CommunityDataLakeRetentionPolicy:
        return cls()

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "accepted_retention_days": self.accepted_retention_days,
            "accepted_retention_max_days": self.accepted_retention_max_days,
            "accepted_retention_min_days": self.accepted_retention_min_days,
            "expired_delete_marker_cleanup": self.expired_delete_marker_cleanup,
            "force_destroy_allowed": self.force_destroy_allowed,
            "incomplete_multipart_cleanup_days": self.incomplete_multipart_cleanup_days,
            "incomplete_multipart_max_days": self.incomplete_multipart_max_days,
            "incomplete_multipart_min_days": self.incomplete_multipart_min_days,
            "limitations": list(self.limitations),
            "noncurrent_version_max_days": self.noncurrent_version_max_days,
            "noncurrent_version_min_days": self.noncurrent_version_min_days,
            "noncurrent_version_retention_days": self.noncurrent_version_retention_days,
            "object_lock_enabled": self.object_lock_enabled,
            "policy_id": self.policy_id,
            "policy_token": self.policy_token,
            "policy_version": self.policy_version,
            "quarantine_retention_days": self.quarantine_retention_days,
            "quarantine_retention_max_days": self.quarantine_retention_max_days,
            "quarantine_retention_min_days": self.quarantine_retention_min_days,
            "review_status": self.review_status,
            "storage_class_transitions_enabled": self.storage_class_transitions_enabled,
            "versioning_enabled": self.versioning_enabled,
        }


def default_retention_policy() -> CommunityDataLakeRetentionPolicy:
    return CommunityDataLakeRetentionPolicy.default()


__all__ = [
    "ACCEPTED_RETENTION_MAX_DAYS",
    "ACCEPTED_RETENTION_MIN_DAYS",
    "COMMUNITY_DATA_LAKE_RETENTION_POLICY_ID",
    "COMMUNITY_DATA_LAKE_RETENTION_POLICY_URN",
    "COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION",
    "CommunityDataLakeRetentionPolicy",
    "DEFAULT_ACCEPTED_RETENTION_DAYS",
    "DEFAULT_INCOMPLETE_MULTIPART_DAYS",
    "DEFAULT_NONCURRENT_VERSION_RETENTION_DAYS",
    "DEFAULT_QUARANTINE_RETENTION_DAYS",
    "INCOMPLETE_MULTIPART_MAX_DAYS",
    "INCOMPLETE_MULTIPART_MIN_DAYS",
    "NONCURRENT_VERSION_MAX_DAYS",
    "NONCURRENT_VERSION_MIN_DAYS",
    "QUARANTINE_RETENTION_MAX_DAYS",
    "QUARANTINE_RETENTION_MIN_DAYS",
    "default_retention_policy",
]

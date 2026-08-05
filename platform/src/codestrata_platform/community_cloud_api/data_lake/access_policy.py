"""Independent Community Data Lake access-control policy (Slice 8.12).

:class:`CommunityDataLakeAccessPolicy` is the Platform-side product-policy
contract for least-privilege Data Lake IAM *intent*. It reconciles with
``infrastructure/modules/community-data-lake/iam.tf`` and the S3 adapter's
actual PutObject / HeadObject (GetObject) calls through static tests — it
does **not** import or override HCL at runtime, and it does **not** attach
any IAM policy.

v0.2.0: writer policy document exists and remains **unattached**.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.access_validation import (
    AccessValidationError,
    validate_access_action_sets,
)

COMMUNITY_DATA_LAKE_ACCESS_POLICY_ID = "community-data-lake-access-policy"
COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION = "1.0"
COMMUNITY_DATA_LAKE_ACCESS_POLICY_URN = (
    f"{COMMUNITY_DATA_LAKE_ACCESS_POLICY_ID}:"
    f"{COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION}"
)

# Actions the future ingestion writer is allowed (maps to adapter calls).
WRITER_ALLOWED_ACTIONS: frozenset[str] = frozenset(
    {
        "s3:PutObject",
        "s3:GetObject",  # HeadObject retry classification uses GetObject IAM
    }
)

WRITER_FORBIDDEN_ACTIONS: frozenset[str] = frozenset(
    {
        "s3:*",
        "s3:ListBucket",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion",
        "s3:DeleteObject*",
        "s3:PutObjectAcl",
        "s3:GetObjectAcl",
        "s3:PutBucketPolicy",
        "s3:GetBucketPolicy",
        "s3:DeleteBucketPolicy",
        "s3:PutLifecycleConfiguration",
        "s3:PutEncryptionConfiguration",
        "s3:PutPublicAccessBlock",
        "s3:PutBucketVersioning",
        "s3:PutBucketOwnershipControls",
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:ReplicateObject",
        "s3:RestoreObject",
        "s3:SelectObjectContent",
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:GenerateDataKey",
        "kms:DescribeKey",
        "kms:*",
    }
)

_ACCEPTED_PREFIX = "raw/"
_QUARANTINE_PREFIX = "quarantine/"

_REVIEW_STATUS = "writer_policy_unattached_least_privilege_foundation"

_LIMITATIONS: tuple[str, ...] = (
    "writer_policy_document_unattached",
    "no_operational_analytics_reader_role",
    "no_operational_quarantine_reader_role",
    "no_list_bucket_for_writer",
    "no_kms_permissions_under_sse_s3",
    "analytics_must_not_auto_include_quarantine",
    "platform_references_infrastructure_does_not_override_hcl",
    "no_endpoint_or_app_wiring",
    "lifecycle_expiration_is_s3_service_not_writer_delete",
)


@dataclass(frozen=True, slots=True)
class CommunityDataLakeAccessPolicy:
    """Deterministic, versioned least-privilege access product-policy contract."""

    policy_id: str = COMMUNITY_DATA_LAKE_ACCESS_POLICY_ID
    policy_version: str = COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION
    writer_allowed_actions: frozenset[str] = WRITER_ALLOWED_ACTIONS
    writer_forbidden_actions: frozenset[str] = WRITER_FORBIDDEN_ACTIONS
    accepted_prefix: str = _ACCEPTED_PREFIX
    quarantine_prefix: str = _QUARANTINE_PREFIX
    retry_read_required: bool = True
    delete_forbidden: bool = True
    list_bucket_allowed: bool = False
    bucket_admin_forbidden: bool = True
    public_access_admin_forbidden: bool = True
    encryption_admin_forbidden: bool = True
    lifecycle_admin_forbidden: bool = True
    kms_permissions_required: bool = False
    analytics_quarantine_separated: bool = True
    writer_policy_attached: bool = False
    review_status: str = _REVIEW_STATUS
    limitations: tuple[str, ...] = _LIMITATIONS

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "writer_allowed_actions", frozenset(self.writer_allowed_actions)
        )
        object.__setattr__(
            self, "writer_forbidden_actions", frozenset(self.writer_forbidden_actions)
        )
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))
        self.validate()

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    def validate(self) -> None:
        if self.policy_id != COMMUNITY_DATA_LAKE_ACCESS_POLICY_ID:
            raise AccessValidationError("unsupported access policy id")
        if self.policy_version != COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION:
            raise AccessValidationError("unsupported access policy version")
        if self.review_status != _REVIEW_STATUS:
            raise AccessValidationError("unsupported access review_status")
        if self.accepted_prefix != _ACCEPTED_PREFIX:
            raise AccessValidationError("accepted_prefix must be 'raw/'")
        if self.quarantine_prefix != _QUARANTINE_PREFIX:
            raise AccessValidationError("quarantine_prefix must be 'quarantine/'")
        if self.writer_policy_attached:
            raise AccessValidationError(
                "writer_policy_attached must be false in v0.2.0 foundation"
            )
        if self.list_bucket_allowed:
            raise AccessValidationError("list_bucket_allowed must be false for the writer")
        if not self.delete_forbidden:
            raise AccessValidationError("delete_forbidden must be true")
        if not self.bucket_admin_forbidden:
            raise AccessValidationError("bucket_admin_forbidden must be true")
        if not self.public_access_admin_forbidden:
            raise AccessValidationError("public_access_admin_forbidden must be true")
        if not self.encryption_admin_forbidden:
            raise AccessValidationError("encryption_admin_forbidden must be true")
        if not self.lifecycle_admin_forbidden:
            raise AccessValidationError("lifecycle_admin_forbidden must be true")
        if self.kms_permissions_required:
            raise AccessValidationError("kms_permissions_required must be false under sse_s3")
        if not self.analytics_quarantine_separated:
            raise AccessValidationError("analytics_quarantine_separated must be true")
        if not self.retry_read_required:
            raise AccessValidationError(
                "retry_read_required must be true (HeadObject uses GetObject IAM)"
            )
        validate_access_action_sets(
            allowed=self.writer_allowed_actions,
            forbidden=self.writer_forbidden_actions,
        )

    @classmethod
    def default(cls) -> CommunityDataLakeAccessPolicy:
        return cls()

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "accepted_prefix": self.accepted_prefix,
            "analytics_quarantine_separated": self.analytics_quarantine_separated,
            "bucket_admin_forbidden": self.bucket_admin_forbidden,
            "delete_forbidden": self.delete_forbidden,
            "encryption_admin_forbidden": self.encryption_admin_forbidden,
            "kms_permissions_required": self.kms_permissions_required,
            "lifecycle_admin_forbidden": self.lifecycle_admin_forbidden,
            "limitations": list(self.limitations),
            "list_bucket_allowed": self.list_bucket_allowed,
            "policy_id": self.policy_id,
            "policy_token": self.policy_token,
            "policy_version": self.policy_version,
            "public_access_admin_forbidden": self.public_access_admin_forbidden,
            "quarantine_prefix": self.quarantine_prefix,
            "retry_read_required": self.retry_read_required,
            "review_status": self.review_status,
            "writer_allowed_actions": sorted(self.writer_allowed_actions),
            "writer_forbidden_actions": sorted(self.writer_forbidden_actions),
            "writer_policy_attached": self.writer_policy_attached,
        }


def default_access_policy() -> CommunityDataLakeAccessPolicy:
    return CommunityDataLakeAccessPolicy.default()


__all__ = [
    "COMMUNITY_DATA_LAKE_ACCESS_POLICY_ID",
    "COMMUNITY_DATA_LAKE_ACCESS_POLICY_URN",
    "COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION",
    "CommunityDataLakeAccessPolicy",
    "WRITER_ALLOWED_ACTIONS",
    "WRITER_FORBIDDEN_ACTIONS",
    "default_access_policy",
]

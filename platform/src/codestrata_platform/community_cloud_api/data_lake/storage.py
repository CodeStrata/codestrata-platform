"""Independent Community Data Lake storage-abstraction policy (Slice 8.13).

:class:`CommunityDataLakeStoragePolicy` is the Platform product-policy
contract for the immutable storage *port*. It does not configure buckets,
wire endpoints, or import AWS SDK clients. OpenTofu and IAM remain separate (Slices
8.1 / 8.12); this policy describes adapter-neutral application intent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.storage_validation import (
    StorageValidationError,
    validate_storage_policy_invariants,
)

COMMUNITY_DATA_LAKE_STORAGE_POLICY_ID = "community-data-lake-storage-policy"
COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION = "1.0"
COMMUNITY_DATA_LAKE_STORAGE_POLICY_URN = (
    f"{COMMUNITY_DATA_LAKE_STORAGE_POLICY_ID}:"
    f"{COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION}"
)

_REVIEW_STATUS = "projected_object_port_unwired_foundation"

_LIMITATIONS: tuple[str, ...] = (
    "no_endpoint_or_app_wiring",
    "no_durable_event_identity_coordination",
    "no_exactly_once_claim",
    "no_transaction_across_identity_and_storage",
    "envelope_put_is_convenience_not_authoritative_for_stream_metadata",
    "in_memory_adapter_is_test_only",
    "s3_adapter_production_capable_but_unwired",
    "production_default_adapter_is_unavailable",
    "no_list_delete_update_admin_surface",
    "iam_requires_put_and_get_only",
)


@dataclass(frozen=True, slots=True)
class CommunityDataLakeStoragePolicy:
    """Deterministic, versioned storage-abstraction product-policy contract."""

    policy_id: str = COMMUNITY_DATA_LAKE_STORAGE_POLICY_ID
    policy_version: str = COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION
    projected_object_authority: bool = True
    accepted_quarantine_methods_separate: bool = True
    envelope_put_authoritative: bool = False
    list_allowed: bool = False
    delete_allowed: bool = False
    update_allowed: bool = False
    bucket_admin_allowed: bool = False
    production_default_unavailable: bool = True
    in_memory_allowed_in_production: bool = False
    writer_policy_attached: bool = False
    review_status: str = _REVIEW_STATUS
    limitations: tuple[str, ...] = _LIMITATIONS

    def __post_init__(self) -> None:
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))
        self.validate()

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    def validate(self) -> None:
        if self.policy_id != COMMUNITY_DATA_LAKE_STORAGE_POLICY_ID:
            raise StorageValidationError("unsupported storage policy id")
        if self.policy_version != COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION:
            raise StorageValidationError("unsupported storage policy version")
        if self.review_status != _REVIEW_STATUS:
            raise StorageValidationError("unsupported storage review_status")
        validate_storage_policy_invariants(self)

    @classmethod
    def default(cls) -> CommunityDataLakeStoragePolicy:
        return cls()

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "accepted_quarantine_methods_separate": self.accepted_quarantine_methods_separate,
            "bucket_admin_allowed": self.bucket_admin_allowed,
            "delete_allowed": self.delete_allowed,
            "envelope_put_authoritative": self.envelope_put_authoritative,
            "in_memory_allowed_in_production": self.in_memory_allowed_in_production,
            "limitations": list(self.limitations),
            "list_allowed": self.list_allowed,
            "policy_id": self.policy_id,
            "policy_token": self.policy_token,
            "policy_version": self.policy_version,
            "production_default_unavailable": self.production_default_unavailable,
            "projected_object_authority": self.projected_object_authority,
            "review_status": self.review_status,
            "update_allowed": self.update_allowed,
            "writer_policy_attached": self.writer_policy_attached,
        }


def default_storage_policy() -> CommunityDataLakeStoragePolicy:
    return CommunityDataLakeStoragePolicy.default()


__all__ = [
    "COMMUNITY_DATA_LAKE_STORAGE_POLICY_ID",
    "COMMUNITY_DATA_LAKE_STORAGE_POLICY_URN",
    "COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION",
    "CommunityDataLakeStoragePolicy",
    "default_storage_policy",
]

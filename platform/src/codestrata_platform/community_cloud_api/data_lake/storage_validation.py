"""Bounded validation for Community Data Lake storage abstraction (Slice 8.13)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from codestrata_platform.community_cloud_api.data_lake.storage import (
        CommunityDataLakeStoragePolicy,
    )


class StorageValidationError(ValueError):
    """Raised when storage-abstraction contracts fail structural validation."""


def validate_storage_policy_invariants(policy: CommunityDataLakeStoragePolicy) -> None:
    """Fail closed if the storage product-policy violates Slice 8.13 invariants."""

    if not policy.projected_object_authority:
        raise StorageValidationError("projected_object_authority must be true")
    if not policy.accepted_quarantine_methods_separate:
        raise StorageValidationError("accepted_quarantine_methods_separate must be true")
    if policy.envelope_put_authoritative:
        raise StorageValidationError(
            "envelope_put_authoritative must be false "
            "(stream metadata requires projected-object puts)"
        )
    if policy.list_allowed or policy.delete_allowed or policy.update_allowed:
        raise StorageValidationError("list/delete/update must remain forbidden")
    if policy.bucket_admin_allowed:
        raise StorageValidationError("bucket_admin_allowed must be false")
    if not policy.production_default_unavailable:
        raise StorageValidationError("production_default_unavailable must be true")
    if policy.in_memory_allowed_in_production:
        raise StorageValidationError("in_memory_allowed_in_production must be false")
    if policy.writer_policy_attached:
        raise StorageValidationError("writer_policy_attached must be false in v0.2.0")


def assert_accepted_storage_object(value: Any) -> None:
    """Reject non-:class:`ImmutableRawStorageObject` values for accepted puts."""

    from codestrata_platform.community_cloud_api.data_lake.objects import (
        ImmutableRawStorageObject,
    )
    from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
        ImmutableQuarantineStorageObject,
    )

    if isinstance(value, ImmutableQuarantineStorageObject):
        raise StorageValidationError("quarantine_object_rejected_by_accepted_method")
    if not isinstance(value, ImmutableRawStorageObject):
        raise StorageValidationError("accepted_method_requires_immutable_raw_storage_object")


def assert_quarantine_storage_object(value: Any) -> None:
    """Reject non-:class:`ImmutableQuarantineStorageObject` values for quarantine puts."""

    from codestrata_platform.community_cloud_api.data_lake.objects import (
        ImmutableRawStorageObject,
    )
    from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
        ImmutableQuarantineStorageObject,
    )

    if isinstance(value, ImmutableRawStorageObject):
        raise StorageValidationError("accepted_object_rejected_by_quarantine_method")
    if not isinstance(value, ImmutableQuarantineStorageObject):
        raise StorageValidationError(
            "quarantine_method_requires_immutable_quarantine_storage_object"
        )


__all__ = [
    "StorageValidationError",
    "assert_accepted_storage_object",
    "assert_quarantine_storage_object",
    "validate_storage_policy_invariants",
]

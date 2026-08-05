"""Canonical JSON serialization for quarantine records (Slice 8.9)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.canonical_json import (
    CanonicalJsonError,
    CanonicalRawJson,
    serialize_canonical_raw_json,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_models import QuarantineRecord
from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
    CommunityDataLakeQuarantinePolicy,
    default_quarantine_policy,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_validation import (
    QuarantineValidationError,
    validate_quarantine_record,
)


class QuarantineSerializationError(ValueError):
    """Raised when a quarantine record cannot be serialized within policy bounds."""


def serialize_quarantine_record(
    record: QuarantineRecord,
    *,
    quarantine_policy: CommunityDataLakeQuarantinePolicy | None = None,
) -> CanonicalRawJson:
    """Serialize a validated quarantine record to canonical storage bytes."""

    policy = quarantine_policy or default_quarantine_policy()
    validate_quarantine_record(record, quarantine_policy=policy)
    try:
        canonical = serialize_canonical_raw_json(record)
    except CanonicalJsonError as exc:
        raise QuarantineSerializationError("quarantine serialization failed") from exc
    if canonical.content_length > policy.max_serialized_record_bytes:
        raise QuarantineSerializationError("quarantine record exceeds max_serialized_record_bytes")
    return canonical

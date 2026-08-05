"""Privacy-safe quarantine storage receipts (Slice 8.9).

Dedicated from :class:`~.receipts.StorageReceipt` so accepted-write receipts
are not polluted with quarantine-only fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus

if TYPE_CHECKING:
    from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
        ImmutableQuarantineStorageObject,
    )

DEFAULT_QUARANTINE_RECEIPT_LIMITATIONS: tuple[str, ...] = (
    "conditional_write_not_transactional_across_retries",
    "no_exactly_once_delivery_guarantee",
    "quarantine_unwired_from_endpoints",
)

QUARANTINE_STREAM_MARKER = "quarantine"


@dataclass(frozen=True, slots=True)
class QuarantineStorageReceipt:
    """Bounded, privacy-safe outcome of one quarantine write attempt.

    NEVER includes ``object_key``, bucket, ETag, version id, ``event_id``,
    or ``installation_id`` in :meth:`to_public_dict`.
    """

    status: StorageWriteStatus
    quarantine_reference: str
    quarantine_reason: str
    quarantine_schema_version: str
    quarantine_policy_token: str
    content_sha256: str
    content_length: int
    object_id: str
    stream_marker: str = QUARANTINE_STREAM_MARKER
    limitations: tuple[str, ...] = ()
    object_key: str | None = None

    def to_public_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "content_length": self.content_length,
            "content_sha256": self.content_sha256,
            "limitations": list(self.limitations),
            "object_id": self.object_id,
            "quarantine_policy_token": self.quarantine_policy_token,
            "quarantine_reason": self.quarantine_reason,
            "quarantine_reference": self.quarantine_reference,
            "quarantine_schema_version": self.quarantine_schema_version,
            "status": self.status.value,
            "stream_marker": self.stream_marker,
        }
        return {key: payload[key] for key in sorted(payload)}

    def to_internal_dict(self) -> dict[str, Any]:
        payload = self.to_public_dict()
        if self.object_key is not None:
            payload["object_key"] = self.object_key
        return {key: payload[key] for key in sorted(payload)}


def build_quarantine_receipt_from_object(
    status: StorageWriteStatus,
    storage_object: ImmutableQuarantineStorageObject,
    *,
    limitations: tuple[str, ...] = DEFAULT_QUARANTINE_RECEIPT_LIMITATIONS,
) -> QuarantineStorageReceipt:
    """Build a :class:`QuarantineStorageReceipt` from a resolved quarantine object."""

    return QuarantineStorageReceipt(
        status=status,
        quarantine_reference=storage_object.quarantine_reference,
        quarantine_reason=storage_object.quarantine_reason,
        quarantine_schema_version=storage_object.quarantine_schema_version,
        quarantine_policy_token=storage_object.quarantine_policy_token,
        content_sha256=storage_object.content_sha256,
        content_length=storage_object.content_length,
        object_id=storage_object.object_id,
        limitations=tuple(sorted(set(limitations))),
        object_key=storage_object.object_key,
    )

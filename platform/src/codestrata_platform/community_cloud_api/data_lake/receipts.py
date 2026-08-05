"""Privacy-safe storage receipts returned from immutable write attempts (Slice 8.2)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.objects import ImmutableRawStorageObject

STORED_OBJECT_REFERENCE_PREFIX = "lake-ref:"
_REFERENCE_HEX_LENGTH = 16

# No adapter in this slice provides an exactly-once delivery guarantee: a
# retried PutObject after a transient failure, or a caller retry after a
# received-but-unacknowledged response, can both legitimately resolve to
# ALREADY_EXISTS. Conditional writes (IfNoneMatch) make concurrent writers
# safe against clobbering, not delivery exactly-once.
DEFAULT_RECEIPT_LIMITATIONS: tuple[str, ...] = (
    "conditional_write_not_transactional_across_retries",
    "no_exactly_once_delivery_guarantee",
)


@dataclass(frozen=True, slots=True)
class StorageReceipt:
    """Bounded, privacy-safe outcome of one immutable write attempt.

    ``object_key`` is INTERNAL only (service-layer / test use) — it is never
    included in :meth:`to_public_dict`, since it is not part of any HTTP
    contract in this slice (Slice 8.2 wires no endpoints to storage).
    """

    status: StorageWriteStatus
    object_id: str
    safe_event_reference: str
    event_stream: str
    content_sha256: str
    content_length: int
    envelope_schema_version: str
    source_schema_version: str
    storage_policy_token: str
    stored_object_reference: str
    limitations: tuple[str, ...] = ()
    object_key: str | None = None

    def to_public_dict(self) -> dict[str, Any]:
        """Bounded dict safe to return to any external caller.

        NEVER includes ``object_key``, bucket, ETag, version id, region, or
        account — only opaque identity/status fields.
        """

        payload: dict[str, Any] = {
            "content_length": self.content_length,
            "content_sha256": self.content_sha256,
            "envelope_schema_version": self.envelope_schema_version,
            "event_stream": self.event_stream,
            "limitations": list(self.limitations),
            "object_id": self.object_id,
            "safe_event_reference": self.safe_event_reference,
            "source_schema_version": self.source_schema_version,
            "status": self.status.value,
            "storage_policy_token": self.storage_policy_token,
            "stored_object_reference": self.stored_object_reference,
        }
        return {key: payload[key] for key in sorted(payload)}

    def to_internal_dict(self) -> dict[str, Any]:
        """Superset of :meth:`to_public_dict` that may include ``object_key``.

        For service-layer / test use only — never returned over HTTP.
        """

        payload = self.to_public_dict()
        if self.object_key is not None:
            payload["object_key"] = self.object_key
        return {key: payload[key] for key in sorted(payload)}


def _stored_object_reference(storage_object: ImmutableRawStorageObject) -> str:
    hex_id = storage_object.opaque_object_id_hex
    if len(hex_id) >= _REFERENCE_HEX_LENGTH:
        fragment = hex_id[:_REFERENCE_HEX_LENGTH]
    else:  # pragma: no cover - defensive; opaque hex is always 24 chars today
        fragment = hashlib.sha256(storage_object.object_id.encode("utf-8")).hexdigest()[
            :_REFERENCE_HEX_LENGTH
        ]
    return f"{STORED_OBJECT_REFERENCE_PREFIX}{fragment}"


def build_receipt_from_object(
    status: StorageWriteStatus,
    storage_object: ImmutableRawStorageObject,
    *,
    limitations: tuple[str, ...] = DEFAULT_RECEIPT_LIMITATIONS,
) -> StorageReceipt:
    """Build a :class:`StorageReceipt` from a resolved storage object and outcome."""

    return StorageReceipt(
        status=status,
        object_id=storage_object.object_id,
        safe_event_reference=storage_object.safe_event_reference,
        event_stream=storage_object.event_stream,
        content_sha256=storage_object.content_sha256,
        content_length=storage_object.content_length,
        envelope_schema_version=storage_object.envelope_schema_version,
        source_schema_version=storage_object.source_schema_version,
        storage_policy_token=storage_object.storage_policy_token,
        stored_object_reference=_stored_object_reference(storage_object),
        limitations=tuple(sorted(set(limitations))),
        object_key=storage_object.object_key,
    )

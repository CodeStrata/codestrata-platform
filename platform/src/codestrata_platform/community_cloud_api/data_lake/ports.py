"""Persistence-neutral Community Data Lake store port (Slices 8.1–8.13).

No ``boto3`` import here or anywhere in this module: production S3/object
storage adapters live under
:mod:`codestrata_platform.community_cloud_api.data_lake.infrastructure`
(Slice 8.2), the only subpackage in this tree allowed to import ``boto3``.
:class:`InMemoryCommunityDataLakeStore` exists for tests only.

Slice 8.13 formalizes the typed projected-object port. Authoritative write
paths are ``put_immutable_storage_object`` / ``put_immutable_quarantine_object``
(aliases ``put_accepted_object`` / ``put_quarantine_object``). Envelope
``put_immutable_event`` remains a convenience helper that rebuilds storage
objects and must not be used for stream-specific metadata preservation.

Nothing here is wired to endpoints / ``app.py`` / ``deployment/wiring.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from codestrata_platform.community_cloud_api.data_lake.canonical_json import (
    CanonicalJsonError,
    validate_utf8_json_object_bytes,
)
from codestrata_platform.community_cloud_api.data_lake.decisions import classify_existing_object
from codestrata_platform.community_cloud_api.data_lake.diagnostics import (
    sanitize_exception_message,
)
from codestrata_platform.community_cloud_api.data_lake.enums import StorageClass, StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.envelopes import (
    DataLakeEnvelope,
    EnvelopeValidationError,
)
from codestrata_platform.community_cloud_api.data_lake.identifiers import LakeIdentifierError
from codestrata_platform.community_cloud_api.data_lake.immutable_write import (
    build_immutable_raw_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.objects import (
    ImmutableRawStorageObject,
    StorageObjectError,
)
from codestrata_platform.community_cloud_api.data_lake.partitions import PartitionKeyError
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.quarantine_identity import (
    QuarantineIdentifierError,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_models import QuarantineRecord
from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
    CommunityDataLakeQuarantinePolicy,
    default_quarantine_policy,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
    ImmutableQuarantineStorageObject,
    QuarantineStorageObjectError,
    build_quarantine_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_receipts import (
    QuarantineStorageReceipt,
    build_quarantine_receipt_from_object,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_serialization import (
    QuarantineSerializationError,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_validation import (
    QuarantineValidationError,
)
from codestrata_platform.community_cloud_api.data_lake.receipts import (
    StorageReceipt,
    build_receipt_from_object,
)
from codestrata_platform.community_cloud_api.data_lake.storage_capabilities import (
    StorageCapabilities,
)
from codestrata_platform.community_cloud_api.data_lake.storage_validation import (
    StorageValidationError,
    assert_accepted_storage_object,
    assert_quarantine_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.validation import DataLakeValidationError


@dataclass(frozen=True, slots=True)
class StorageWriteResult:
    """Outcome of a single store write attempt.

    ``object_key`` is an internal coordination field. Prefer
    :meth:`to_public_dict` for logging/API-safe serialization (omits the key).
    """

    status: StorageWriteStatus
    object_key: str | None = None
    detail: str = ""
    receipt: StorageReceipt | None = None
    quarantine_receipt: QuarantineStorageReceipt | None = None
    storage_class: StorageClass | None = None

    def to_public_dict(self) -> dict[str, Any]:
        """Safe serialization — never includes ``object_key``."""

        from codestrata_platform.community_cloud_api.data_lake.storage_results import (
            storage_result_to_public_dict,
        )

        return storage_result_to_public_dict(self)

    def to_stable_dict(self) -> dict[str, Any]:
        """Deterministic dump including internal ``object_key`` when present.

        Prefer :meth:`to_public_dict` for external/safe surfaces.
        """

        payload: dict[str, Any] = {"status": self.status.value}
        if self.storage_class is not None:
            payload["storage_class"] = self.storage_class.value
        if self.object_key is not None:
            payload["object_key"] = self.object_key
        if self.detail:
            payload["detail"] = self.detail
        if self.receipt is not None:
            payload["receipt"] = self.receipt.to_public_dict()
        if self.quarantine_receipt is not None:
            payload["quarantine_receipt"] = self.quarantine_receipt.to_public_dict()
        return {key: payload[key] for key in sorted(payload)}


# Backward-compatible re-export — QuarantineRecord moved to quarantine_models
# in Slice 8.9; ports remains the historical import path for callers/tests.
__all__ = [
    "CommunityDataLakeStore",
    "InMemoryCommunityDataLakeStore",
    "QuarantineRecord",
    "StorageWriteResult",
]


class CommunityDataLakeStore(Protocol):
    """Persistence-neutral port implemented by concrete storage adapters.

    Authoritative methods accept fully projected immutable storage objects.
    Envelope helpers remain for tests/compatibility only.
    """

    def put_immutable_storage_object(
        self, storage_object: ImmutableRawStorageObject
    ) -> StorageWriteResult: ...

    def put_immutable_quarantine_object(
        self, storage_object: ImmutableQuarantineStorageObject
    ) -> StorageWriteResult: ...

    def put_immutable_event(self, envelope: DataLakeEnvelope) -> StorageWriteResult: ...

    def quarantine_event(self, record: QuarantineRecord) -> StorageWriteResult: ...


_STORE_ERRORS = (
    DataLakeValidationError,
    PartitionKeyError,
    LakeIdentifierError,
    EnvelopeValidationError,
    CanonicalJsonError,
    StorageObjectError,
    QuarantineValidationError,
    QuarantineSerializationError,
    QuarantineStorageObjectError,
    QuarantineIdentifierError,
)


@dataclass
class InMemoryCommunityDataLakeStore:
    """Test-only in-memory store enforcing the package's immutability semantics.

    Semantics:

    - Writing the same logical object twice with identical content is an
      idempotent replay (``ALREADY_EXISTS``), not an error.
    - Writing the same object key with different content is a ``CONFLICT``
      and never overwrites the original.
    - ``unavailable=True`` simulates a storage backend outage.
    - Accepted and quarantine objects occupy separate namespaces.

    Never selected implicitly for production — use the storage factory with
    ``allow_in_memory_test=True`` only from tests.
    """

    policy: CommunityDataLakePolicy = field(default_factory=CommunityDataLakePolicy.default)
    quarantine_policy: CommunityDataLakeQuarantinePolicy = field(
        default_factory=default_quarantine_policy
    )
    unavailable: bool = False
    _accepted_objects: dict[str, dict[str, Any]] = field(
        default_factory=dict, init=False, repr=False
    )
    _quarantined_objects: dict[str, dict[str, Any]] = field(
        default_factory=dict, init=False, repr=False
    )

    @property
    def capabilities(self) -> StorageCapabilities:
        if self.unavailable:
            return StorageCapabilities.for_unavailable()
        return StorageCapabilities.for_in_memory_test()

    def put_accepted_object(
        self, storage_object: ImmutableRawStorageObject
    ) -> StorageWriteResult:
        return self.put_immutable_storage_object(storage_object)

    def put_quarantine_object(
        self, storage_object: ImmutableQuarantineStorageObject
    ) -> StorageWriteResult:
        return self.put_immutable_quarantine_object(storage_object)

    def put_immutable_event(self, envelope: DataLakeEnvelope) -> StorageWriteResult:
        if self.unavailable:
            return StorageWriteResult(
                status=StorageWriteStatus.UNAVAILABLE,
                detail="store_unavailable",
                storage_class=StorageClass.ACCEPTED,
            )
        try:
            storage_object = build_immutable_raw_storage_object(envelope, self.policy)
        except _STORE_ERRORS as exc:
            return StorageWriteResult(
                status=StorageWriteStatus.REJECTED,
                detail=sanitize_exception_message(exc),
                storage_class=StorageClass.ACCEPTED,
            )
        return self._put_storage_object(storage_object, envelope_dict=envelope.to_stable_dict())

    def put_immutable_storage_object(
        self, storage_object: ImmutableRawStorageObject
    ) -> StorageWriteResult:
        """Store an already-resolved :class:`ImmutableRawStorageObject` directly."""

        try:
            assert_accepted_storage_object(storage_object)
        except StorageValidationError as exc:
            return StorageWriteResult(
                status=StorageWriteStatus.REJECTED,
                detail=str(exc),
                storage_class=StorageClass.ACCEPTED,
            )
        if self.unavailable:
            return StorageWriteResult(
                status=StorageWriteStatus.UNAVAILABLE,
                detail="store_unavailable",
                storage_class=StorageClass.ACCEPTED,
            )
        try:
            storage_object.validate()
            envelope_dict = validate_utf8_json_object_bytes(storage_object.canonical_json_bytes)
        except (StorageObjectError, CanonicalJsonError) as exc:
            return StorageWriteResult(
                status=StorageWriteStatus.REJECTED,
                detail=sanitize_exception_message(exc),
                storage_class=StorageClass.ACCEPTED,
            )
        return self._put_storage_object(storage_object, envelope_dict=envelope_dict)

    def _put_storage_object(
        self,
        storage_object: ImmutableRawStorageObject,
        *,
        envelope_dict: dict[str, Any],
    ) -> StorageWriteResult:
        object_key = storage_object.object_key
        if object_key.startswith("quarantine/"):
            return StorageWriteResult(
                status=StorageWriteStatus.REJECTED,
                detail="accepted_key_must_use_raw_prefix",
                storage_class=StorageClass.ACCEPTED,
            )
        existing = self._accepted_objects.get(object_key)
        if existing is not None:
            outcome = classify_existing_object(
                requested_digest=storage_object.content_sha256,
                stored_digest=existing.get("content_sha256"),
            )
            if outcome is StorageWriteStatus.ALREADY_EXISTS:
                receipt = build_receipt_from_object(StorageWriteStatus.ALREADY_EXISTS, storage_object)
                return StorageWriteResult(
                    status=StorageWriteStatus.ALREADY_EXISTS,
                    object_key=object_key,
                    receipt=receipt,
                    storage_class=StorageClass.ACCEPTED,
                )
            return StorageWriteResult(
                status=StorageWriteStatus.CONFLICT,
                object_key=object_key,
                storage_class=StorageClass.ACCEPTED,
            )

        self._accepted_objects[object_key] = {
            "bytes": storage_object.canonical_json_bytes,
            "content_sha256": storage_object.content_sha256,
            "envelope_dict": envelope_dict,
            "extra_s3_metadata": dict(storage_object.extra_s3_metadata),
            "object_key": object_key,
        }
        receipt = build_receipt_from_object(StorageWriteStatus.STORED, storage_object)
        return StorageWriteResult(
            status=StorageWriteStatus.STORED,
            object_key=object_key,
            receipt=receipt,
            storage_class=StorageClass.ACCEPTED,
        )

    def quarantine_event(self, record: QuarantineRecord) -> StorageWriteResult:
        """Project ``record`` then store under the quarantine namespace."""

        if self.unavailable:
            return StorageWriteResult(
                status=StorageWriteStatus.UNAVAILABLE,
                detail="store_unavailable",
                storage_class=StorageClass.QUARANTINE,
            )
        try:
            storage_object = build_quarantine_storage_object(
                record,
                quarantine_policy=self.quarantine_policy,
                data_lake_policy=self.policy,
            )
        except _STORE_ERRORS as exc:
            return StorageWriteResult(
                status=StorageWriteStatus.REJECTED,
                detail=sanitize_exception_message(exc),
                storage_class=StorageClass.QUARANTINE,
            )
        return self.put_immutable_quarantine_object(storage_object)

    def put_immutable_quarantine_object(
        self, storage_object: ImmutableQuarantineStorageObject
    ) -> StorageWriteResult:
        """Store an already-resolved quarantine object (byte-exact / test path)."""

        try:
            assert_quarantine_storage_object(storage_object)
        except StorageValidationError as exc:
            return StorageWriteResult(
                status=StorageWriteStatus.REJECTED,
                detail=str(exc),
                storage_class=StorageClass.QUARANTINE,
            )
        if self.unavailable:
            return StorageWriteResult(
                status=StorageWriteStatus.UNAVAILABLE,
                detail="store_unavailable",
                storage_class=StorageClass.QUARANTINE,
            )
        try:
            storage_object.validate()
            record_dict = validate_utf8_json_object_bytes(storage_object.canonical_json_bytes)
        except (QuarantineStorageObjectError, CanonicalJsonError, StorageObjectError) as exc:
            return StorageWriteResult(
                status=StorageWriteStatus.REJECTED,
                detail=sanitize_exception_message(exc),
                storage_class=StorageClass.QUARANTINE,
            )

        object_key = storage_object.object_key
        if not object_key.startswith("quarantine/"):
            return StorageWriteResult(
                status=StorageWriteStatus.REJECTED,
                detail="quarantine_key_must_use_quarantine_prefix",
                storage_class=StorageClass.QUARANTINE,
            )
        if object_key.startswith("raw/"):
            return StorageWriteResult(
                status=StorageWriteStatus.REJECTED,
                detail="quarantine_key_must_not_use_raw_prefix",
                storage_class=StorageClass.QUARANTINE,
            )

        existing = self._quarantined_objects.get(object_key)
        if existing is not None:
            outcome = classify_existing_object(
                requested_digest=storage_object.content_sha256,
                stored_digest=existing.get("content_sha256"),
            )
            if outcome is StorageWriteStatus.ALREADY_EXISTS:
                receipt = build_quarantine_receipt_from_object(
                    StorageWriteStatus.ALREADY_EXISTS, storage_object
                )
                return StorageWriteResult(
                    status=StorageWriteStatus.ALREADY_EXISTS,
                    object_key=object_key,
                    quarantine_receipt=receipt,
                    storage_class=StorageClass.QUARANTINE,
                )
            return StorageWriteResult(
                status=StorageWriteStatus.CONFLICT,
                object_key=object_key,
                storage_class=StorageClass.QUARANTINE,
            )

        self._quarantined_objects[object_key] = {
            "bytes": storage_object.canonical_json_bytes,
            "content_sha256": storage_object.content_sha256,
            "record_dict": record_dict,
            "extra_s3_metadata": dict(storage_object.extra_s3_metadata),
            "object_key": object_key,
        }
        receipt = build_quarantine_receipt_from_object(StorageWriteStatus.STORED, storage_object)
        return StorageWriteResult(
            status=StorageWriteStatus.STORED,
            object_key=object_key,
            quarantine_receipt=receipt,
            storage_class=StorageClass.QUARANTINE,
        )

    def get_accepted_extra_s3_metadata(self, object_key: str) -> dict[str, str] | None:
        """Test helper: return a copy of preserved stream S3 metadata, if any."""

        stored = self._accepted_objects.get(object_key)
        if stored is None:
            return None
        return dict(stored.get("extra_s3_metadata") or {})

    def get_accepted_content(self, object_key: str) -> dict[str, Any] | None:
        """Test helper: return a copy of the stored envelope dict, if any."""

        stored = self._accepted_objects.get(object_key)
        return None if stored is None else dict(stored["envelope_dict"])

    def get_accepted_bytes(self, object_key: str) -> bytes | None:
        """Test helper: return the exact stored canonical JSON bytes, if any."""

        stored = self._accepted_objects.get(object_key)
        return None if stored is None else stored["bytes"]

    def get_accepted_digest(self, object_key: str) -> str | None:
        """Test helper: return the stored ``sha256:`` content digest, if any."""

        stored = self._accepted_objects.get(object_key)
        return None if stored is None else stored["content_sha256"]

    def get_quarantined_content(self, object_key: str) -> dict[str, Any] | None:
        """Test helper: return a copy of the parsed quarantine record dict, if any."""

        stored = self._quarantined_objects.get(object_key)
        return None if stored is None else dict(stored["record_dict"])

    def get_quarantined_bytes(self, object_key: str) -> bytes | None:
        """Test helper: return the exact stored quarantine canonical JSON bytes."""

        stored = self._quarantined_objects.get(object_key)
        return None if stored is None else stored["bytes"]

    def get_quarantined_digest(self, object_key: str) -> str | None:
        """Test helper: return the stored quarantine ``sha256:`` content digest."""

        stored = self._quarantined_objects.get(object_key)
        return None if stored is None else stored["content_sha256"]

    def accepted_object_keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._accepted_objects))

    def quarantined_object_keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._quarantined_objects))

    def clear(self) -> None:
        self._accepted_objects.clear()
        self._quarantined_objects.clear()

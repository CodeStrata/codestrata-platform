"""Production-capable, unwired S3 adapter for the Community Data Lake (Slice 8.2 / 8.9).

No ``boto3`` import here — this adapter is constructed with an injected
:class:`~.client.S3ClientPort` (a real boto3 client satisfies this
structurally; see :func:`~.client.create_boto3_s3_client`). Nothing in this
module is called by ``app.py``, ``deployment/wiring.py``, or any endpoint
service in this slice: the adapter exists and is fully unit-testable, but is
not wired into production request handling.

No exactly-once delivery is claimed anywhere in this module: conditional
writes (``IfNoneMatch: "*"``) make concurrent writers safe against
clobbering, not delivery exactly-once. A retried ``PutObject`` after a
transient failure, or a caller retry after a received-but-unacknowledged
response, may both legitimately resolve to ``ALREADY_EXISTS``.

``put_immutable_event``, ``put_immutable_storage_object``,
``quarantine_event``, and ``put_immutable_quarantine_object`` are exposed —
no delete, update, or list methods exist on this adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from codestrata_platform.community_cloud_api.data_lake.canonical_json import checksum_sha256_b64
from codestrata_platform.community_cloud_api.data_lake.decisions import classify_existing_object
from codestrata_platform.community_cloud_api.data_lake.diagnostics import sanitize_exception_message
from codestrata_platform.community_cloud_api.data_lake.enums import (
    EncryptionMode,
    StorageClass,
    StorageWriteStatus,
)
from codestrata_platform.community_cloud_api.data_lake.envelopes import DataLakeEnvelope
from codestrata_platform.community_cloud_api.data_lake.errors import StorageErrorCategory
from codestrata_platform.community_cloud_api.data_lake.immutable_write import (
    build_immutable_raw_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.client import S3ClientPort
from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3DataLakeStoreConfiguration,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.error_mapping import (
    is_transient_storage_error,
    map_s3_exception,
)
from codestrata_platform.community_cloud_api.data_lake.objects import (
    ImmutableRawStorageObject,
    StorageObjectError,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.ports import QuarantineRecord, StorageWriteResult
from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
    CommunityDataLakeQuarantinePolicy,
    default_quarantine_policy,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
    ImmutableQuarantineStorageObject,
    build_quarantine_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_receipts import (
    build_quarantine_receipt_from_object,
)
from codestrata_platform.community_cloud_api.data_lake.receipts import build_receipt_from_object
from codestrata_platform.community_cloud_api.data_lake.storage_capabilities import (
    StorageCapabilities,
)
from codestrata_platform.community_cloud_api.data_lake.storage_validation import (
    StorageValidationError,
    assert_accepted_storage_object,
    assert_quarantine_storage_object,
)

_StorageObject = Union[ImmutableRawStorageObject, ImmutableQuarantineStorageObject]


@dataclass(frozen=True, slots=True, kw_only=True)
class CommunityDataLakeS3Store:
    """S3-backed :class:`~.ports.CommunityDataLakeStore` adapter (unwired).

    Immutability semantics mirror :class:`~.ports.InMemoryCommunityDataLakeStore`:
    a first write to a key is ``STORED``; an identical-digest replay is
    ``ALREADY_EXISTS``; a different-digest write to the same key is
    ``CONFLICT`` and the original object is never overwritten (enforced by
    the S3 ``IfNoneMatch: "*"`` conditional write, not client-side logic).
    """

    config: S3DataLakeStoreConfiguration
    policy: CommunityDataLakePolicy
    client: S3ClientPort
    quarantine_policy: CommunityDataLakeQuarantinePolicy | None = None

    @property
    def capabilities(self) -> StorageCapabilities:
        return StorageCapabilities.for_s3()

    def _quarantine_policy(self) -> CommunityDataLakeQuarantinePolicy:
        return self.quarantine_policy or default_quarantine_policy()

    def put_accepted_object(
        self, storage_object: ImmutableRawStorageObject
    ) -> StorageWriteResult:
        return self.put_immutable_storage_object(storage_object)

    def put_quarantine_object(
        self, storage_object: ImmutableQuarantineStorageObject
    ) -> StorageWriteResult:
        return self.put_immutable_quarantine_object(storage_object)

    def put_immutable_event(self, envelope: DataLakeEnvelope) -> StorageWriteResult:
        try:
            storage_object = build_immutable_raw_storage_object(envelope, self.policy)
        except Exception as exc:  # noqa: BLE001 - domain validation errors only, sanitized below
            return StorageWriteResult(
                status=StorageWriteStatus.REJECTED,
                detail=sanitize_exception_message(exc),
                storage_class=StorageClass.ACCEPTED,
            )
        return self._put_accepted_storage_object(storage_object)

    def put_immutable_storage_object(
        self, storage_object: ImmutableRawStorageObject
    ) -> StorageWriteResult:
        """Store an already-resolved :class:`ImmutableRawStorageObject` directly."""

        try:
            assert_accepted_storage_object(storage_object)
            storage_object.validate()
        except (StorageValidationError, Exception) as exc:  # noqa: BLE001
            detail = (
                str(exc)
                if isinstance(exc, StorageValidationError)
                else sanitize_exception_message(exc)
            )
            return StorageWriteResult(
                status=StorageWriteStatus.REJECTED,
                detail=detail,
                storage_class=StorageClass.ACCEPTED,
            )
        return self._put_accepted_storage_object(storage_object)

    def quarantine_event(self, record: QuarantineRecord) -> StorageWriteResult:
        """Project and persist a quarantine record under ``quarantine/``."""

        try:
            storage_object = build_quarantine_storage_object(
                record,
                quarantine_policy=self._quarantine_policy(),
                data_lake_policy=self.policy,
            )
        except Exception as exc:  # noqa: BLE001 - domain validation errors only, sanitized below
            return StorageWriteResult(
                status=StorageWriteStatus.REJECTED,
                detail=sanitize_exception_message(exc),
                storage_class=StorageClass.QUARANTINE,
            )
        return self.put_immutable_quarantine_object(storage_object)

    def put_immutable_quarantine_object(
        self, storage_object: ImmutableQuarantineStorageObject
    ) -> StorageWriteResult:
        """Store an already-resolved quarantine object (byte-exact path)."""

        try:
            assert_quarantine_storage_object(storage_object)
            storage_object.validate()
        except (StorageValidationError, Exception) as exc:  # noqa: BLE001
            detail = (
                str(exc)
                if isinstance(exc, StorageValidationError)
                else sanitize_exception_message(exc)
            )
            return StorageWriteResult(
                status=StorageWriteStatus.REJECTED,
                detail=detail,
                storage_class=StorageClass.QUARANTINE,
            )
        return self._put_quarantine_storage_object(storage_object)

    def _put_accepted_storage_object(
        self, storage_object: ImmutableRawStorageObject
    ) -> StorageWriteResult:
        attempts = 0
        while True:
            attempts += 1
            try:
                self._put_object(storage_object)
            except Exception as exc:  # noqa: BLE001 - narrowed immediately via map_s3_exception
                status, category, safe_code = map_s3_exception(exc)
                if category is StorageErrorCategory.PRECONDITION:
                    return self._resolve_precondition_accepted(storage_object)
                if is_transient_storage_error(category) and attempts < self.config.max_attempts:
                    continue
                return StorageWriteResult(
                    status=status,
                    detail=safe_code,
                    storage_class=StorageClass.ACCEPTED,
                )
            else:
                receipt = build_receipt_from_object(StorageWriteStatus.STORED, storage_object)
                return StorageWriteResult(
                    status=StorageWriteStatus.STORED,
                    object_key=storage_object.object_key,
                    receipt=receipt,
                    storage_class=StorageClass.ACCEPTED,
                )

    def _put_quarantine_storage_object(
        self, storage_object: ImmutableQuarantineStorageObject
    ) -> StorageWriteResult:
        attempts = 0
        while True:
            attempts += 1
            try:
                self._put_object(storage_object)
            except Exception as exc:  # noqa: BLE001 - narrowed immediately via map_s3_exception
                status, category, safe_code = map_s3_exception(exc)
                if category is StorageErrorCategory.PRECONDITION:
                    return self._resolve_precondition_quarantine(storage_object)
                if is_transient_storage_error(category) and attempts < self.config.max_attempts:
                    continue
                return StorageWriteResult(
                    status=status,
                    detail=safe_code,
                    storage_class=StorageClass.QUARANTINE,
                )
            else:
                receipt = build_quarantine_receipt_from_object(
                    StorageWriteStatus.STORED, storage_object
                )
                return StorageWriteResult(
                    status=StorageWriteStatus.STORED,
                    object_key=storage_object.object_key,
                    quarantine_receipt=receipt,
                    storage_class=StorageClass.QUARANTINE,
                )

    def _put_object(self, storage_object: _StorageObject) -> None:
        kwargs: dict[str, object] = {
            "Bucket": self.config.bucket_name,
            "Key": storage_object.object_key,
            "Body": storage_object.canonical_json_bytes,
            "ContentType": storage_object.content_type,
            "ContentLength": storage_object.content_length,
            # REQUIRED — never omit: this is the only thing preventing a
            # silent overwrite of an existing immutable object.
            "IfNoneMatch": "*",
            "Metadata": storage_object.to_s3_metadata(),
        }
        if self.config.checksum_required:
            kwargs["ChecksumSHA256"] = checksum_sha256_b64(storage_object.canonical_json_bytes)
        # Slice 8.11: never omit encryption and never fall back to unencrypted.
        # Configuration already rejects non-sse_s3; this branch fails closed if
        # that invariant is ever violated.
        if self.config.encryption_mode == EncryptionMode.SSE_S3.value:
            kwargs["ServerSideEncryption"] = "AES256"
        else:
            raise StorageObjectError(
                "encryption_mode_unsupported: only sse_s3/AES256 PutObject is permitted"
            )
        if "SSEKMSKeyId" in kwargs or "SSECustomerKey" in kwargs:
            raise StorageObjectError("kms_key_forbidden: customer keys are not permitted in sse_s3")
        self.client.put_object(**kwargs)

    def _resolve_precondition_accepted(
        self, storage_object: ImmutableRawStorageObject
    ) -> StorageWriteResult:
        """Resolve a ``PreconditionFailed`` with exactly one ``head_object`` call."""

        try:
            head = self.client.head_object(
                Bucket=self.config.bucket_name, Key=storage_object.object_key
            )
        except Exception as exc:  # noqa: BLE001 - narrowed via map_s3_exception
            status, _category, safe_code = map_s3_exception(exc)
            return StorageWriteResult(
                status=status,
                detail=safe_code,
                storage_class=StorageClass.ACCEPTED,
            )

        metadata = head.get("Metadata") if isinstance(head, dict) else None
        stored_digest = (metadata or {}).get(self.config.metadata_digest_key)
        outcome = classify_existing_object(
            requested_digest=storage_object.content_sha256, stored_digest=stored_digest
        )
        if outcome is StorageWriteStatus.ALREADY_EXISTS:
            receipt = build_receipt_from_object(StorageWriteStatus.ALREADY_EXISTS, storage_object)
            return StorageWriteResult(
                status=StorageWriteStatus.ALREADY_EXISTS,
                object_key=storage_object.object_key,
                receipt=receipt,
                storage_class=StorageClass.ACCEPTED,
            )
        return StorageWriteResult(
            status=StorageWriteStatus.CONFLICT,
            object_key=storage_object.object_key,
            storage_class=StorageClass.ACCEPTED,
        )

    def _resolve_precondition_quarantine(
        self, storage_object: ImmutableQuarantineStorageObject
    ) -> StorageWriteResult:
        """Resolve a quarantine ``PreconditionFailed`` with one ``head_object`` call."""

        try:
            head = self.client.head_object(
                Bucket=self.config.bucket_name, Key=storage_object.object_key
            )
        except Exception as exc:  # noqa: BLE001 - narrowed via map_s3_exception
            status, _category, safe_code = map_s3_exception(exc)
            return StorageWriteResult(
                status=status,
                detail=safe_code,
                storage_class=StorageClass.QUARANTINE,
            )

        metadata = head.get("Metadata") if isinstance(head, dict) else None
        stored_digest = (metadata or {}).get(self.config.metadata_digest_key)
        outcome = classify_existing_object(
            requested_digest=storage_object.content_sha256, stored_digest=stored_digest
        )
        if outcome is StorageWriteStatus.ALREADY_EXISTS:
            receipt = build_quarantine_receipt_from_object(
                StorageWriteStatus.ALREADY_EXISTS, storage_object
            )
            return StorageWriteResult(
                status=StorageWriteStatus.ALREADY_EXISTS,
                object_key=storage_object.object_key,
                quarantine_receipt=receipt,
                storage_class=StorageClass.QUARANTINE,
            )
        return StorageWriteResult(
            status=StorageWriteStatus.CONFLICT,
            object_key=storage_object.object_key,
            storage_class=StorageClass.QUARANTINE,
        )

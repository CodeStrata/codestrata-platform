"""Community Data Lake enums and vocabularies (Slice 8.1)."""

from __future__ import annotations

from enum import Enum


class EventStream(str, Enum):
    """Source Community Cloud API domains eligible for lake archival."""

    TELEMETRY = "telemetry"
    ASSESSMENT_METADATA = "assessment_metadata"
    CLI_EVENT = "cli_event"
    EXTENSION_EVENT = "extension_event"
    AI_USAGE = "ai_usage"


class QuarantineReasonCode(str, Enum):
    """Bounded reasons an event is diverted to the quarantine prefix.

    ``UNSUPPORTED_SCHEMA`` is retained as a generic backward-compatible code;
    prefer the more specific ``UNSUPPORTED_*`` codes for new call sites.
    """

    INVALID_ENVELOPE = "invalid_envelope"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    UNSUPPORTED_ENVELOPE_SCHEMA = "unsupported_envelope_schema"
    UNSUPPORTED_SOURCE_SCHEMA = "unsupported_source_schema"
    UNSUPPORTED_SOURCE_POLICY = "unsupported_source_policy"
    STREAM_CONTRACT_MISMATCH = "stream_contract_mismatch"
    INVALID_SOURCE_PAYLOAD = "invalid_source_payload"
    ENVELOPE_TOO_LARGE = "envelope_too_large"
    INVALID_PARTITION = "invalid_partition"
    INVALID_STORAGE_OBJECT = "invalid_storage_object"
    CHECKSUM_MISMATCH = "checksum_mismatch"
    MALFORMED_STORED_OBJECT = "malformed_stored_object"
    UNSAFE_PAYLOAD = "unsafe_payload"
    SERIALIZATION_FAILURE = "serialization_failure"
    STORAGE_KEY_FAILURE = "storage_key_failure"
    STORAGE_REJECTED = "storage_rejected"


class QuarantineValidationStage(str, Enum):
    """Bounded stage at which a quarantine decision was made."""

    REQUEST_VALIDATION = "request_validation"
    ENVELOPE_PROJECTION = "envelope_projection"
    ENVELOPE_VALIDATION = "envelope_validation"
    PARTITION_PROJECTION = "partition_projection"
    STORAGE_OBJECT_VALIDATION = "storage_object_validation"
    STORAGE_WRITE = "storage_write"
    STORAGE_READ_VERIFICATION = "storage_read_verification"


class StorageWriteStatus(str, Enum):
    """Outcome of a single immutable-object write attempt."""

    STORED = "stored"
    ALREADY_EXISTS = "already_exists"
    CONFLICT = "conflict"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"


class StorageClass(str, Enum):
    """Namespace class for an immutable write result (Slice 8.13)."""

    ACCEPTED = "accepted"
    QUARANTINE = "quarantine"


class EncryptionMode(str, Enum):
    """Server-side encryption mode for lake objects.

    ``SSE_S3`` is the Slice 8.1 default. ``SSE_KMS`` is reserved for a future
    migration and is not selectable by policy defaults yet.
    """

    SSE_S3 = "sse_s3"
    SSE_KMS = "sse_kms"

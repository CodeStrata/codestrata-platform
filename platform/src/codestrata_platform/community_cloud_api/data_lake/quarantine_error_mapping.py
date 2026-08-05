"""Map domain validation failures to quarantine reason codes (Slice 8.9).

Never includes exception strings in the returned mapping — only allowlisted
reason codes, validation stages, and diagnostic codes. Storage-unavailable
failures are **not** mapped to quarantine as malformed-data by default.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.canonical_json import CanonicalJsonError
from codestrata_platform.community_cloud_api.data_lake.enums import (
    QuarantineReasonCode,
    QuarantineValidationStage,
)
from codestrata_platform.community_cloud_api.data_lake.envelope_models import EnvelopeErrorCode
from codestrata_platform.community_cloud_api.data_lake.envelopes import EnvelopeValidationError
from codestrata_platform.community_cloud_api.data_lake.errors import (
    DataLakeStorageError,
    StorageErrorCategory,
)
from codestrata_platform.community_cloud_api.data_lake.identifiers import LakeIdentifierError
from codestrata_platform.community_cloud_api.data_lake.objects import StorageObjectError
from codestrata_platform.community_cloud_api.data_lake.partitions import PartitionKeyError
from codestrata_platform.community_cloud_api.data_lake.quarantine_serialization import (
    QuarantineSerializationError,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_validation import (
    QuarantineValidationError,
)
from codestrata_platform.community_cloud_api.data_lake.validation import DataLakeValidationError


@dataclass(frozen=True, slots=True)
class QuarantineErrorMapping:
    """Bounded mapping from a domain failure to quarantine decision material."""

    quarantine_reason: str
    validation_stage: str
    diagnostic_codes: tuple[str, ...]
    should_quarantine: bool = True

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "diagnostic_codes": list(self.diagnostic_codes),
            "quarantine_reason": self.quarantine_reason,
            "should_quarantine": self.should_quarantine,
            "validation_stage": self.validation_stage,
        }


_ENVELOPE_ERROR_TO_REASON: dict[str, str] = {
    EnvelopeErrorCode.INVALID_ENVELOPE.value: QuarantineReasonCode.INVALID_ENVELOPE.value,
    EnvelopeErrorCode.UNSUPPORTED_ENVELOPE_SCHEMA.value: (
        QuarantineReasonCode.UNSUPPORTED_ENVELOPE_SCHEMA.value
    ),
    EnvelopeErrorCode.UNSUPPORTED_SOURCE_SCHEMA.value: (
        QuarantineReasonCode.UNSUPPORTED_SOURCE_SCHEMA.value
    ),
    EnvelopeErrorCode.UNSUPPORTED_SOURCE_POLICY.value: (
        QuarantineReasonCode.UNSUPPORTED_SOURCE_POLICY.value
    ),
    EnvelopeErrorCode.STREAM_CONTRACT_MISMATCH.value: (
        QuarantineReasonCode.STREAM_CONTRACT_MISMATCH.value
    ),
    EnvelopeErrorCode.INVALID_SOURCE_PAYLOAD.value: (
        QuarantineReasonCode.INVALID_SOURCE_PAYLOAD.value
    ),
    EnvelopeErrorCode.UNSAFE_ENVELOPE.value: QuarantineReasonCode.UNSAFE_PAYLOAD.value,
    EnvelopeErrorCode.ENVELOPE_TOO_LARGE.value: QuarantineReasonCode.ENVELOPE_TOO_LARGE.value,
    EnvelopeErrorCode.ENVELOPE_SERIALIZATION_FAILED.value: (
        QuarantineReasonCode.SERIALIZATION_FAILURE.value
    ),
    EnvelopeErrorCode.ENVELOPE_DESERIALIZATION_FAILED.value: (
        QuarantineReasonCode.SERIALIZATION_FAILURE.value
    ),
}

_PARTITION_CODE_TO_DIAGNOSTIC: dict[str, str] = {
    "stream_mismatch": "stream_mismatch",
    "unsupported_envelope_schema": "unsupported_envelope_schema",
    "unsupported_source_schema": "unsupported_source_schema",
    "unsupported_source_policy": "unsupported_source_policy",
    "invalid_payload": "invalid_payload",
    "partition_invalid": "partition_invalid",
    "storage_object_invalid": "invalid_storage_object",
}


def map_exception_to_quarantine(exc: BaseException) -> QuarantineErrorMapping | None:
    """Map ``exc`` to quarantine material, or ``None`` when quarantine is inappropriate.

    Returns ``None`` (do not quarantine as malformed-data) for transient /
    unavailable storage failures. Never embeds ``str(exc)``.
    """

    if isinstance(exc, DataLakeStorageError):
        if exc.category in (
            StorageErrorCategory.TRANSIENT,
            StorageErrorCategory.TIMEOUT,
            StorageErrorCategory.ACCESS_DENIED,
            StorageErrorCategory.UNKNOWN,
        ):
            return QuarantineErrorMapping(
                quarantine_reason=QuarantineReasonCode.STORAGE_REJECTED.value,
                validation_stage=QuarantineValidationStage.STORAGE_WRITE.value,
                diagnostic_codes=("storage_dependency_unavailable",),
                should_quarantine=False,
            )
        if exc.category is StorageErrorCategory.CHECKSUM_MISMATCH:
            return QuarantineErrorMapping(
                quarantine_reason=QuarantineReasonCode.CHECKSUM_MISMATCH.value,
                validation_stage=QuarantineValidationStage.STORAGE_READ_VERIFICATION.value,
                diagnostic_codes=("checksum_mismatch",),
            )
        if exc.category is StorageErrorCategory.PRECONDITION:
            return QuarantineErrorMapping(
                quarantine_reason=QuarantineReasonCode.STORAGE_REJECTED.value,
                validation_stage=QuarantineValidationStage.STORAGE_WRITE.value,
                diagnostic_codes=("conditional_write_conflict",),
                should_quarantine=False,
            )

    if isinstance(exc, EnvelopeValidationError):
        # EnvelopeValidationError historically carries a message; prefer generic
        # invalid_envelope unless a known EnvelopeErrorCode value is present.
        message = getattr(exc, "code", None) or ""
        if isinstance(message, EnvelopeErrorCode):
            code = message.value
        else:
            code = str(message) if message else ""
        reason = _ENVELOPE_ERROR_TO_REASON.get(code, QuarantineReasonCode.INVALID_ENVELOPE.value)
        diagnostic = code if code in _ENVELOPE_ERROR_TO_REASON else "invalid_envelope"
        return QuarantineErrorMapping(
            quarantine_reason=reason,
            validation_stage=QuarantineValidationStage.ENVELOPE_VALIDATION.value,
            diagnostic_codes=(diagnostic,),
        )

    code_attr = getattr(exc, "code", None)
    if isinstance(code_attr, str) and code_attr in _PARTITION_CODE_TO_DIAGNOSTIC:
        diagnostic = _PARTITION_CODE_TO_DIAGNOSTIC[code_attr]
        if diagnostic in ("unsupported_envelope_schema", "unsupported_source_schema"):
            reason = diagnostic
        elif diagnostic == "unsupported_source_policy":
            reason = QuarantineReasonCode.UNSUPPORTED_SOURCE_POLICY.value
        elif diagnostic == "stream_mismatch":
            reason = QuarantineReasonCode.STREAM_CONTRACT_MISMATCH.value
        elif diagnostic == "invalid_storage_object":
            reason = QuarantineReasonCode.INVALID_STORAGE_OBJECT.value
        else:
            reason = QuarantineReasonCode.INVALID_PARTITION.value
        return QuarantineErrorMapping(
            quarantine_reason=reason,
            validation_stage=QuarantineValidationStage.PARTITION_PROJECTION.value,
            diagnostic_codes=(diagnostic,),
        )

    if isinstance(exc, StorageObjectError):
        return QuarantineErrorMapping(
            quarantine_reason=QuarantineReasonCode.INVALID_STORAGE_OBJECT.value,
            validation_stage=QuarantineValidationStage.STORAGE_OBJECT_VALIDATION.value,
            diagnostic_codes=("invalid_storage_object",),
        )

    if isinstance(exc, (CanonicalJsonError, QuarantineSerializationError)):
        return QuarantineErrorMapping(
            quarantine_reason=QuarantineReasonCode.SERIALIZATION_FAILURE.value,
            validation_stage=QuarantineValidationStage.ENVELOPE_PROJECTION.value,
            diagnostic_codes=("serialization_failure",),
        )

    if isinstance(exc, (PartitionKeyError, LakeIdentifierError)):
        return QuarantineErrorMapping(
            quarantine_reason=QuarantineReasonCode.STORAGE_KEY_FAILURE.value,
            validation_stage=QuarantineValidationStage.PARTITION_PROJECTION.value,
            diagnostic_codes=("key_validation_failed",),
        )

    if isinstance(exc, QuarantineValidationError):
        return QuarantineErrorMapping(
            quarantine_reason=QuarantineReasonCode.INVALID_ENVELOPE.value,
            validation_stage=QuarantineValidationStage.ENVELOPE_VALIDATION.value,
            diagnostic_codes=("invalid_envelope",),
            should_quarantine=False,
        )

    if isinstance(exc, DataLakeValidationError):
        text = str(type(exc).__name__)
        del text
        return QuarantineErrorMapping(
            quarantine_reason=QuarantineReasonCode.INVALID_PARTITION.value,
            validation_stage=QuarantineValidationStage.PARTITION_PROJECTION.value,
            diagnostic_codes=("invalid_partition",),
        )

    return None

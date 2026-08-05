"""Re-export hub for Data Lake envelope domain types and the error taxonomy (Slice 8.3).

Kept minimal and import-cheap, mirroring the existing :mod:`.models`
re-export module — gives callers a single obvious surface for "the Slice 8.3
envelope types" without needing to know which concrete module defines each.
"""

from __future__ import annotations

from enum import Enum

from codestrata_platform.community_cloud_api.data_lake.envelopes import (
    DataLakeEnvelope,
    DataLakeEventEnvelope,
    EnvelopeAcceptance,
    EnvelopeClient,
    EnvelopeIdentity,
    EnvelopeValidationError,
    SourceContract,
)


class EnvelopeErrorCode(str, Enum):
    """Bounded, stable error taxonomy for Slice 8.3 envelope construction/validation.

    Every value is a short, safe identifier only — never raw exception
    text, payload fragments, or file paths.
    """

    INVALID_ENVELOPE = "invalid_envelope"
    UNSUPPORTED_ENVELOPE_SCHEMA = "unsupported_envelope_schema"
    UNSUPPORTED_SOURCE_SCHEMA = "unsupported_source_schema"
    UNSUPPORTED_SOURCE_POLICY = "unsupported_source_policy"
    STREAM_CONTRACT_MISMATCH = "stream_contract_mismatch"
    INVALID_SOURCE_PAYLOAD = "invalid_source_payload"
    UNSAFE_ENVELOPE = "unsafe_envelope"
    ENVELOPE_TOO_LARGE = "envelope_too_large"
    ENVELOPE_SERIALIZATION_FAILED = "envelope_serialization_failed"
    ENVELOPE_DESERIALIZATION_FAILED = "envelope_deserialization_failed"


__all__ = [
    "DataLakeEnvelope",
    "DataLakeEventEnvelope",
    "EnvelopeAcceptance",
    "EnvelopeClient",
    "EnvelopeErrorCode",
    "EnvelopeIdentity",
    "EnvelopeValidationError",
    "SourceContract",
]

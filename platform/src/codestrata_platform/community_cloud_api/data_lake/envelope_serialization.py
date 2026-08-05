"""Slice 8.3 envelope-level serialize/deserialize helpers.

This module does **not** invent a second serializer: it wraps the Slice 8.2
canonical JSON primitives
(:func:`~.canonical_json.serialize_canonical_raw_json`,
:func:`~.canonical_json.validate_utf8_json_object_bytes`) with envelope-aware
fail-closed structure checks, nested-object reconstruction, and (by default)
re-validation of the deserialized payload against its registered source
contract.
"""

from __future__ import annotations

from typing import Any

from codestrata_platform.community_cloud_api.data_lake.canonical_json import (
    CanonicalJsonError,
    CanonicalRawJson,
    serialize_canonical_raw_json,
    validate_utf8_json_object_bytes,
)
from codestrata_platform.community_cloud_api.data_lake.envelope_models import EnvelopeErrorCode
from codestrata_platform.community_cloud_api.data_lake.envelope_validation import (
    EnvelopeBuildError,
    revalidate_payload_against_source_contract,
)
from codestrata_platform.community_cloud_api.data_lake.envelopes import (
    DataLakeEnvelope,
    EnvelopeAcceptance,
    EnvelopeClient,
    EnvelopeIdentity,
    EnvelopeValidationError,
    SourceContract,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy

_TOP_LEVEL_FIELDS = frozenset(
    {
        "acceptance",
        "client",
        "envelope_schema_version",
        "event_stream",
        "identity",
        "payload",
        "source_contract",
    }
)
_SOURCE_CONTRACT_FIELDS = frozenset({"policy_id", "schema_name", "schema_version"})
_IDENTITY_FIELDS = frozenset({"event_key", "safe_event_reference"})
_ACCEPTANCE_FIELDS = frozenset({"accepted_at", "partition_date"})
_CLIENT_FIELDS = frozenset({"client_type"})


def serialize_data_lake_envelope(envelope: DataLakeEnvelope) -> CanonicalRawJson:
    """Serialize ``envelope`` to canonical storage bytes.

    Thin wrapper over :func:`~.canonical_json.serialize_canonical_raw_json`
    that translates :class:`~.canonical_json.CanonicalJsonError` into the
    bounded Slice 8.3 :class:`EnvelopeBuildError` taxonomy.
    """

    try:
        return serialize_canonical_raw_json(envelope)
    except CanonicalJsonError as exc:
        raise EnvelopeBuildError(EnvelopeErrorCode.ENVELOPE_SERIALIZATION_FAILED) from exc


def _require_object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EnvelopeValidationError(f"{name} must be a JSON object")
    return value


def _require_exact_fields(value: dict[str, Any], allowed: frozenset[str], name: str) -> None:
    actual = set(value)
    if actual - allowed:
        raise EnvelopeValidationError(f"{name} has unknown field(s): {sorted(actual - allowed)}")
    if allowed - actual:
        raise EnvelopeValidationError(f"{name} is missing field(s): {sorted(allowed - actual)}")


def _build_source_contract(value: Any) -> SourceContract:
    obj = _require_object(value, "source_contract")
    _require_exact_fields(obj, _SOURCE_CONTRACT_FIELDS, "source_contract")
    return SourceContract(
        schema_name=obj["schema_name"],
        schema_version=obj["schema_version"],
        policy_id=obj["policy_id"],
    )


def _build_identity(value: Any) -> EnvelopeIdentity:
    obj = _require_object(value, "identity")
    _require_exact_fields(obj, _IDENTITY_FIELDS, "identity")
    return EnvelopeIdentity(
        event_key=obj["event_key"], safe_event_reference=obj["safe_event_reference"]
    )


def _build_acceptance(value: Any) -> EnvelopeAcceptance:
    obj = _require_object(value, "acceptance")
    _require_exact_fields(obj, _ACCEPTANCE_FIELDS, "acceptance")
    return EnvelopeAcceptance(accepted_at=obj["accepted_at"], partition_date=obj["partition_date"])


def _build_client(value: Any) -> EnvelopeClient:
    obj = _require_object(value, "client")
    _require_exact_fields(obj, _CLIENT_FIELDS, "client")
    return EnvelopeClient(client_type=obj["client_type"])


def deserialize_data_lake_envelope(
    data: bytes,
    *,
    policy: CommunityDataLakePolicy | None = None,
    revalidate_payload: bool = True,
) -> DataLakeEnvelope:
    """Reconstruct a validated :class:`DataLakeEnvelope` from canonical bytes.

    Fail-closed at every step:

    1. ``data`` must be valid UTF-8 JSON with an object root.
    2. Every top-level and nested-object field set must match exactly —
       unknown fields are rejected, missing fields are rejected.
    3. ``envelope_schema_version`` must exactly equal ``policy``'s.
    4. The reconstructed envelope is re-validated against ``policy``
       (privacy scan + size bound).
    5. When ``revalidate_payload`` (default), the payload is re-validated
       against its registered source contract's request model and
       allowlisted projector — not just checked for well-formed JSON.
    """

    active = policy or CommunityDataLakePolicy.default()
    try:
        parsed = validate_utf8_json_object_bytes(data)
    except CanonicalJsonError as exc:
        raise EnvelopeBuildError(EnvelopeErrorCode.ENVELOPE_DESERIALIZATION_FAILED) from exc

    try:
        _require_exact_fields(parsed, _TOP_LEVEL_FIELDS, "envelope")
        envelope_schema_version = parsed["envelope_schema_version"]
        if not isinstance(envelope_schema_version, str):
            raise EnvelopeValidationError("envelope_schema_version must be a string")
        if envelope_schema_version != active.envelope_schema_version:
            raise EnvelopeBuildError(EnvelopeErrorCode.UNSUPPORTED_ENVELOPE_SCHEMA)

        event_stream = parsed["event_stream"]
        if not isinstance(event_stream, str):
            raise EnvelopeValidationError("event_stream must be a string")

        payload = parsed["payload"]
        if not isinstance(payload, dict):
            raise EnvelopeValidationError("payload must be a JSON object")

        envelope = DataLakeEnvelope(
            envelope_schema_version=envelope_schema_version,
            event_stream=event_stream,
            source_contract=_build_source_contract(parsed["source_contract"]),
            identity=_build_identity(parsed["identity"]),
            acceptance=_build_acceptance(parsed["acceptance"]),
            client=_build_client(parsed["client"]),
            payload=payload,
        )
    except EnvelopeBuildError:
        raise
    except EnvelopeValidationError as exc:
        raise EnvelopeBuildError(EnvelopeErrorCode.INVALID_ENVELOPE) from exc

    try:
        envelope.validate_against_policy(active)
    except EnvelopeValidationError as exc:
        message = str(exc)
        code = (
            EnvelopeErrorCode.ENVELOPE_TOO_LARGE
            if "max_envelope_bytes" in message
            else EnvelopeErrorCode.UNSAFE_ENVELOPE
        )
        raise EnvelopeBuildError(code) from exc

    if revalidate_payload:
        revalidate_payload_against_source_contract(envelope)

    return envelope

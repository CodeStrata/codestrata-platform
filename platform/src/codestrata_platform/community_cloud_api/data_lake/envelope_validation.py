"""Fail-closed Slice 8.3 envelope build/validation errors and guard helpers.

Every guard here raises :class:`EnvelopeBuildError` carrying a bounded
:class:`~.envelope_models.EnvelopeErrorCode` — never the underlying
exception text, payload fragments, or file paths. This is the single error
type that :mod:`.envelope_builders` and :mod:`.envelope_serialization`
raise for all Slice 8.3 fail-closed rejections.
"""

from __future__ import annotations

from typing import Any

from codestrata_platform.community_cloud_api.data_lake.envelope_models import EnvelopeErrorCode
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy

_MAX_DETAIL_LENGTH = 64


class EnvelopeBuildError(ValueError):
    """Raised for any Slice 8.3 fail-closed envelope build/validate failure."""

    def __init__(self, code: EnvelopeErrorCode, detail: str = "") -> None:
        bounded_detail = (detail or "")[:_MAX_DETAIL_LENGTH]
        message = code.value if not bounded_detail else f"{code.value}: {bounded_detail}"
        super().__init__(message)
        self.code = code
        self.detail = bounded_detail

    def to_stable_dict(self) -> dict[str, str]:
        payload: dict[str, str] = {"code": self.code.value}
        if self.detail:
            payload["detail"] = self.detail
        return {key: payload[key] for key in sorted(payload)}


def require_supported_envelope_schema_version(
    actual: str, policy: CommunityDataLakePolicy
) -> None:
    if actual != policy.envelope_schema_version:
        raise EnvelopeBuildError(EnvelopeErrorCode.UNSUPPORTED_ENVELOPE_SCHEMA)


def require_supported_source_schema_version(
    actual: str, expected: str | frozenset[str] | set[str] | tuple[str, ...]
) -> None:
    if isinstance(expected, str):
        if actual != expected:
            raise EnvelopeBuildError(EnvelopeErrorCode.UNSUPPORTED_SOURCE_SCHEMA)
        return
    if actual not in expected:
        raise EnvelopeBuildError(EnvelopeErrorCode.UNSUPPORTED_SOURCE_SCHEMA)


def require_supported_source_policy(actual: str, expected: str) -> None:
    if actual != expected:
        raise EnvelopeBuildError(EnvelopeErrorCode.UNSUPPORTED_SOURCE_POLICY)


def require_matching_request_model(request: Any, expected_model: type) -> None:
    if not isinstance(request, expected_model):
        raise EnvelopeBuildError(EnvelopeErrorCode.STREAM_CONTRACT_MISMATCH)


def require_allowed_client_type(client_type: str, allowed: frozenset[str]) -> None:
    if client_type not in allowed:
        raise EnvelopeBuildError(
            EnvelopeErrorCode.STREAM_CONTRACT_MISMATCH, "client_type_not_allowed"
        )


def require_bounded_size(serialized_size: int, policy: CommunityDataLakePolicy) -> None:
    if serialized_size > policy.max_envelope_bytes:
        raise EnvelopeBuildError(EnvelopeErrorCode.ENVELOPE_TOO_LARGE)


def revalidate_payload_against_source_contract(envelope: Any) -> None:
    """Re-validate ``envelope.payload`` against its registered request model.

    Used after deserialization (untrusted bytes) to confirm the payload
    still round-trips through the same Pydantic model and allowlisted
    projector as when it was first built — not merely that the JSON is
    well-formed. Imports the registry lazily to avoid a module-load-time
    dependency from every envelope-validation caller onto every endpoint
    package.
    """

    from codestrata_platform.community_cloud_api.data_lake.envelope_registry import (
        UnknownEventStreamError,
        get_source_contract,
    )

    try:
        descriptor = get_source_contract(envelope.event_stream)
    except UnknownEventStreamError as exc:
        raise EnvelopeBuildError(EnvelopeErrorCode.INVALID_ENVELOPE, "unknown_event_stream") from exc

    if envelope.source_contract.schema_name != descriptor.schema_name:
        raise EnvelopeBuildError(EnvelopeErrorCode.UNSUPPORTED_SOURCE_SCHEMA, "schema_name_mismatch")
    supported = descriptor.supported_schema_versions or frozenset({descriptor.schema_version})
    require_supported_source_schema_version(
        envelope.source_contract.schema_version, supported
    )
    require_supported_source_policy(envelope.source_contract.policy_id, descriptor.policy_id)

    try:
        model_instance = descriptor.request_model.model_validate(dict(envelope.payload))
    except Exception as exc:  # pydantic ValidationError, or any projector-shape mismatch
        raise EnvelopeBuildError(EnvelopeErrorCode.INVALID_SOURCE_PAYLOAD) from exc

    reprojected = descriptor.project_payload(model_instance)
    if reprojected != dict(envelope.payload):
        raise EnvelopeBuildError(
            EnvelopeErrorCode.INVALID_SOURCE_PAYLOAD, "payload_projection_mismatch"
        )

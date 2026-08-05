"""High-level, typed Data Lake envelope construction from endpoint requests (Slice 8.3).

This is the entry point every future call site should use to turn an
already-validated endpoint request model into a
:class:`~.envelopes.DataLakeEnvelope`: look up the stream's registered
source contract, confirm the request matches it, project the allowlisted
payload, extract and validate the client type, stamp acceptance time from an
:class:`~.accepted_clock.AcceptanceClock`, and construct + validate the
envelope. Nothing in this module is imported by ``app.py``,
``deployment/wiring.py``, or any endpoint ``routes.py``/``service.py`` — it
remains unwired, exactly like the rest of this package.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from codestrata_platform.community_cloud_api.data_lake.accepted_clock import (
    AcceptanceClock,
    format_accepted_at,
    partition_date_from_accepted_at,
)
from codestrata_platform.community_cloud_api.data_lake.enums import EventStream
from codestrata_platform.community_cloud_api.data_lake.envelope_models import EnvelopeErrorCode
from codestrata_platform.community_cloud_api.data_lake.envelope_registry import (
    UnknownEventStreamError,
    get_source_contract,
)
from codestrata_platform.community_cloud_api.data_lake.envelope_validation import EnvelopeBuildError
from codestrata_platform.community_cloud_api.data_lake.envelopes import (
    DataLakeEnvelope,
    EnvelopeAcceptance,
    EnvelopeClient,
    EnvelopeIdentity,
    EnvelopeValidationError,
    SourceContract,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.validation.models import CommunityApiRequestModel

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids a runtime import cycle
    from codestrata_platform.community_cloud_api.data_lake.objects import ImmutableRawStorageObject
    from codestrata_platform.community_cloud_api.data_lake.ports import (
        CommunityDataLakeStore,
        StorageWriteResult,
    )


def build_data_lake_envelope(
    *,
    event_stream: EventStream | str,
    request: CommunityApiRequestModel,
    event_key: str,
    safe_event_reference: str,
    clock: AcceptanceClock,
    policy: CommunityDataLakePolicy | None = None,
) -> DataLakeEnvelope:
    """Build a validated :class:`DataLakeEnvelope` from a typed endpoint request.

    Raises :class:`EnvelopeBuildError` (never a raw ``ValueError``/pydantic
    error) for every rejection path, with a bounded
    :class:`EnvelopeErrorCode`:

    - ``invalid_envelope`` — unknown/unregistered event stream.
    - ``stream_contract_mismatch`` — ``request`` is not an instance of the
      stream's registered request model, or ``client_type`` is not
      allowlisted for the stream.
    - ``invalid_source_payload`` — the registered projector/extractor
      raised while processing an otherwise type-matching request.
    - ``unsafe_envelope`` — the constructed envelope failed structural or
      privacy validation.
    - ``envelope_too_large`` — the serialized envelope exceeds
      ``policy.max_envelope_bytes``.
    """

    active_policy = policy or CommunityDataLakePolicy.default()
    try:
        descriptor = get_source_contract(event_stream)
    except UnknownEventStreamError as exc:
        raise EnvelopeBuildError(EnvelopeErrorCode.INVALID_ENVELOPE, "unknown_event_stream") from exc

    if not isinstance(request, descriptor.request_model):
        raise EnvelopeBuildError(EnvelopeErrorCode.STREAM_CONTRACT_MISMATCH)

    try:
        payload = descriptor.project_payload(request)
        client_type = descriptor.client_type_extractor(request)
    except EnvelopeBuildError:
        raise
    except Exception as exc:  # defensive: a projector/extractor bug must never leak payload
        raise EnvelopeBuildError(EnvelopeErrorCode.INVALID_SOURCE_PAYLOAD) from exc

    if client_type not in descriptor.allowed_client_types:
        raise EnvelopeBuildError(
            EnvelopeErrorCode.STREAM_CONTRACT_MISMATCH, "client_type_not_allowed"
        )

    accepted_at = format_accepted_at(clock.now_utc())
    partition_date = partition_date_from_accepted_at(accepted_at)

    try:
        envelope = DataLakeEnvelope(
            envelope_schema_version=active_policy.envelope_schema_version,
            event_stream=descriptor.event_stream.value,
            source_contract=SourceContract(
                schema_name=descriptor.schema_name,
                schema_version=descriptor.schema_version,
                policy_id=descriptor.policy_id,
            ),
            identity=EnvelopeIdentity(
                event_key=event_key, safe_event_reference=safe_event_reference
            ),
            acceptance=EnvelopeAcceptance(accepted_at=accepted_at, partition_date=partition_date),
            client=EnvelopeClient(client_type=client_type),
            payload=payload,
        )
    except EnvelopeValidationError as exc:
        raise EnvelopeBuildError(EnvelopeErrorCode.INVALID_ENVELOPE) from exc

    try:
        envelope.validate_against_policy(active_policy)
    except EnvelopeValidationError as exc:
        message = str(exc)
        code = (
            EnvelopeErrorCode.ENVELOPE_TOO_LARGE
            if "max_envelope_bytes" in message
            else EnvelopeErrorCode.UNSAFE_ENVELOPE
        )
        raise EnvelopeBuildError(code) from exc

    return envelope


def build_storage_object_from_request(
    *,
    event_stream: EventStream | str,
    request: CommunityApiRequestModel,
    event_key: str,
    safe_event_reference: str,
    clock: AcceptanceClock,
    policy: CommunityDataLakePolicy | None = None,
) -> "ImmutableRawStorageObject":
    """End-to-end: typed request -> envelope -> resolved storage object.

    Thin composition over :func:`build_data_lake_envelope` and
    :func:`~.immutable_write.build_immutable_raw_storage_object`, kept here
    (rather than in ``immutable_write.py``) so that module never has to
    import endpoint request models or the stream registry.
    """

    from codestrata_platform.community_cloud_api.data_lake.immutable_write import (
        build_immutable_raw_storage_object,
    )

    active_policy = policy or CommunityDataLakePolicy.default()
    envelope = build_data_lake_envelope(
        event_stream=event_stream,
        request=request,
        event_key=event_key,
        safe_event_reference=safe_event_reference,
        clock=clock,
        policy=active_policy,
    )
    return build_immutable_raw_storage_object(envelope, active_policy)


def put_request_via_store(
    store: "CommunityDataLakeStore",
    *,
    event_stream: EventStream | str,
    request: CommunityApiRequestModel,
    event_key: str,
    safe_event_reference: str,
    clock: AcceptanceClock,
    policy: CommunityDataLakePolicy | None = None,
) -> "StorageWriteResult":
    """Convenience: build the envelope, then write it via ``store.put_immutable_event``.

    Still no endpoint/HTTP wiring — ``store`` must be constructed and
    supplied by the caller (e.g. a future slice's service layer or a test).
    """

    envelope = build_data_lake_envelope(
        event_stream=event_stream,
        request=request,
        event_key=event_key,
        safe_event_reference=safe_event_reference,
        clock=clock,
        policy=policy,
    )
    return store.put_immutable_event(envelope)

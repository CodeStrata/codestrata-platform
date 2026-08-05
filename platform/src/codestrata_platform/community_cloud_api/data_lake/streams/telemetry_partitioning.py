"""Telemetry stream partitioning: policy + storage-object projection (Slice 8.5).

Binds the generic Slice 8.4 partition-policy and diagnostics machinery
(:mod:`~codestrata_platform.community_cloud_api.data_lake.partition_policies`,
:mod:`~codestrata_platform.community_cloud_api.data_lake.stream_partitions`,
:mod:`~codestrata_platform.community_cloud_api.data_lake.partition_diagnostics`,
:mod:`~codestrata_platform.community_cloud_api.data_lake.stream_storage`) to
the second concrete stream: ``telemetry``. Nothing in this module (or
anything it imports) is called by ``app.py``, ``deployment/wiring.py``, or
any endpoint service — see
``platform/tests/community_cloud_api/data_lake/test_telemetry_partition_boundary.py``.

## Partition dimension decision (Slice 8.5)

The accepted object key for this stream is the **generic Hive path only**,
identical in shape to the ``assessment_metadata`` stream from Slice 8.4::

    raw/stream=telemetry/schema_version=1.0/year=YYYY/month=MM/day=DD/{opaque}.json

No additional path dimension is added for ``client_type`` or
``event_type``. Rationale:

- **Cross-stream path consistency.** Keeping every stream's accepted path at
  exactly `stream=` / `schema_version=` / `year=` / `month=` / `day=`
  simplifies any future shared Glue/Athena catalog definition across all
  five streams, matching the Slice 8.4 decision for ``assessment_metadata``.
- **Avoid lifecycle/prefix fragmentation.** Splitting the ``raw/stream=
  telemetry/...`` prefix by client type or event type would multiply the
  number of S3 prefixes (and any future lifecycle/retention rule scoped to
  them) without a corresponding reader in this repository today.
- **``client_type`` vocabulary is small but unnecessary as a path
  dimension.** :class:`~codestrata_platform.community_cloud_api.telemetry.enums.TelemetryClientName`
  has exactly three bounded members — low cardinality — but the value is
  already carried in S3 metadata (see below) and in the private payload's
  ``client.name`` field, so a fourth copy in the path buys nothing.
- **``event_type`` couples storage layout to analytics semantics.** Unlike
  ``client_type`` (a stable transport-classification concept),
  :class:`~codestrata_platform.community_cloud_api.telemetry.enums.TelemetryEventType`
  is a product/analytics vocabulary that is expected to evolve as new
  telemetry events are added. Baking it into the physical storage path
  would force a partition-layout migration every time the event-type
  vocabulary changes. ``event_type`` therefore stays private-payload-only —
  never in the path, never in S3 metadata.

## S3 metadata decision (Slice 8.5)

Exactly one new, optional S3 metadata key is added:
``codestrata-client-type`` — the envelope's ``client.client_type`` value
(one of :class:`~codestrata_platform.community_cloud_api.telemetry.enums.TelemetryClientName`'s
three members), attached only by
:func:`project_telemetry_storage_object`. No other telemetry field is ever
promoted to metadata: not ``codestrata-telemetry-event-type`` (``event_type``
remains private payload only, per the dimension decision above), not
``installation_id``, ``event_id``, ``occurred_at``, ``feature``,
``operation``, ``duration_bucket``, ``outcome``, or ``flags`` — see
``forbidden_partition_fields`` below and
``platform/docs/community-cloud-api/telemetry-data-lake.md`` for the full
property-cardinality review this decision is based on.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from codestrata_platform.community_cloud_api.data_lake.enums import EventStream
from codestrata_platform.community_cloud_api.data_lake.envelopes import DataLakeEnvelope
from codestrata_platform.community_cloud_api.data_lake.immutable_write import (
    build_immutable_raw_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.objects import (
    ALLOWED_S3_METADATA_KEYS,
    StorageObjectError,
)
from codestrata_platform.community_cloud_api.data_lake.partition_diagnostics import (
    PartitionProjectionDiagnostics,
)
from codestrata_platform.community_cloud_api.data_lake.partition_policies import (
    StreamPartitionPolicy,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.receipts import (
    STORED_OBJECT_REFERENCE_PREFIX,
)
from codestrata_platform.community_cloud_api.data_lake.stream_partitions import (
    StreamPartitionError,
    assert_partition_key_matches_policy,
    assert_s3_metadata_matches_policy,
)
from codestrata_platform.community_cloud_api.data_lake.stream_storage import (
    StorageProjectionResult,
    merge_extra_s3_metadata,
)
from codestrata_platform.community_cloud_api.telemetry.enums import TelemetryClientName
from codestrata_platform.community_cloud_api.telemetry.models import TelemetryIngestionRequest
from codestrata_platform.community_cloud_api.telemetry.policy import (
    COMMUNITY_TELEMETRY_POLICY_URN,
    COMMUNITY_TELEMETRY_SCHEMA_VERSION,
)

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids a runtime import cycle
    from codestrata_platform.community_cloud_api.data_lake.ports import (
        CommunityDataLakeStore,
        StorageWriteResult,
    )

TELEMETRY_PARTITION_POLICY_ID = "community-telemetry-partition-policy"
TELEMETRY_PARTITION_POLICY_VERSION = "1.0"
TELEMETRY_PARTITION_POLICY_URN = (
    f"{TELEMETRY_PARTITION_POLICY_ID}:{TELEMETRY_PARTITION_POLICY_VERSION}"
)

# Informational only — never part of the partition path (see module
# docstring for the dimension decision). Optional on the resulting object:
# only ``project_telemetry_storage_object`` attaches it.
CLIENT_TYPE_METADATA_KEY = "codestrata-client-type"

_SUPPORTED_ENVELOPE_SCHEMA_VERSIONS = frozenset({"1.0"})
_SUPPORTED_SOURCE_SCHEMA_VERSIONS = frozenset({COMMUNITY_TELEMETRY_SCHEMA_VERSION})
_SUPPORTED_SOURCE_POLICY_IDS = frozenset({COMMUNITY_TELEMETRY_POLICY_URN})

_TELEMETRY_CLIENT_TYPES: frozenset[str] = frozenset(item.value for item in TelemetryClientName)

# Field names that must never become a partition path dimension for this
# stream — enforced structurally by ``stream_partitions`` against the parsed
# Hive dimension names of any candidate key, independent of (and in addition
# to) the "generic dimensions only" decision above. Deliberately broad: it
# covers every approved-private telemetry field plus a handful of
# cross-stream identity/shape fields that must never leak into any stream's
# partition path.
_FORBIDDEN_PARTITION_FIELDS: frozenset[str] = frozenset(
    {
        "event_id",
        "installation_id",
        "request_id",
        "ip",
        "ip_address",
        "client_type",
        "client_version",
        "platform",
        "event_type",
        "occurred_at",
        "feature",
        "operation",
        "outcome",
        "duration_bucket",
        "count",
        "flags",
        "properties",
        "language",
        "executed_heads",
        "repository_name",
        "repository_url",
        "assessment_status",
        "assessment_schema_version",
    }
)

_LIMITATIONS: tuple[str, ...] = (
    "no_extra_partition_dimensions_in_v0_2_0",
    "client_type_in_metadata_not_path",
    "event_type_remains_private_payload",
    "occurred_at_not_partition_date",
    "installation_id_private_payload_only",
    "no_store_wiring_this_module_only_projects",
)

# Bounded, allowlisted rejection codes for ``PartitionProjectionError`` — see
# class docstring. No payload/exception text is ever included beyond one of
# these short, stable identifiers plus an optional bounded detail fragment.
ALLOWED_PARTITION_PROJECTION_ERROR_CODES: frozenset[str] = frozenset(
    {
        "stream_mismatch",
        "unsupported_envelope_schema",
        "unsupported_source_schema",
        "unsupported_source_policy",
        "invalid_payload",
        "invalid_client_type",
        "partition_invalid",
        "storage_object_invalid",
    }
)

_MAX_ERROR_DETAIL_LENGTH = 64


class PartitionProjectionError(ValueError):
    """Raised for every fail-closed rejection while projecting a storage object.

    ``code`` must be one of :data:`ALLOWED_PARTITION_PROJECTION_ERROR_CODES`
    — never raw exception text, payload fragments, or file paths.
    """

    def __init__(self, code: str, detail: str = "") -> None:
        if code not in ALLOWED_PARTITION_PROJECTION_ERROR_CODES:
            raise ValueError(f"unregistered PartitionProjectionError code: {code!r}")
        bounded_detail = (detail or "")[:_MAX_ERROR_DETAIL_LENGTH]
        message = code if not bounded_detail else f"{code}: {bounded_detail}"
        super().__init__(message)
        self.code = code
        self.detail = bounded_detail

    def to_stable_dict(self) -> dict[str, str]:
        payload: dict[str, str] = {"code": self.code}
        if self.detail:
            payload["detail"] = self.detail
        return {key: payload[key] for key in sorted(payload)}


def default_telemetry_partition_policy() -> StreamPartitionPolicy:
    """The Slice 8.5 partition policy for the ``telemetry`` stream."""

    return StreamPartitionPolicy(
        policy_id=TELEMETRY_PARTITION_POLICY_ID,
        policy_version=TELEMETRY_PARTITION_POLICY_VERSION,
        event_stream=EventStream.TELEMETRY,
        supported_envelope_schema_versions=_SUPPORTED_ENVELOPE_SCHEMA_VERSIONS,
        supported_source_schema_versions=_SUPPORTED_SOURCE_SCHEMA_VERSIONS,
        supported_source_policy_ids=_SUPPORTED_SOURCE_POLICY_IDS,
        supported_assessment_schema_versions=frozenset(),
        s3_metadata_allowlist=frozenset(ALLOWED_S3_METADATA_KEYS),
        forbidden_partition_fields=_FORBIDDEN_PARTITION_FIELDS,
        limitations=_LIMITATIONS,
    )


def _require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise PartitionProjectionError(code, detail)


def project_telemetry_storage_object(
    envelope: DataLakeEnvelope,
    *,
    data_lake_policy: CommunityDataLakePolicy | None = None,
    partition_policy: StreamPartitionPolicy | None = None,
) -> StorageProjectionResult:
    """Validate ``envelope`` and resolve it into a partition-checked storage object.

    Order of checks (every failure raises :class:`PartitionProjectionError`
    with a bounded, allowlisted code — see module-level constant):

    1. ``stream_mismatch`` — ``envelope.event_stream`` must be
       ``"telemetry"``.
    2. ``unsupported_envelope_schema`` / ``unsupported_source_schema`` /
       ``unsupported_source_policy`` — envelope/source identity must match
       the partition policy's supported sets.
    3. ``invalid_payload`` — ``payload`` must round-trip through
       :class:`TelemetryIngestionRequest` (fail-closed typed re-check); this
       also rejects a corrupted/unsupported ``event_type`` since the model's
       own field validator enforces the
       :class:`~codestrata_platform.community_cloud_api.telemetry.enums.TelemetryEventType`
       allowlist.
    4. ``invalid_client_type`` — ``envelope.client.client_type`` must be one
       of :class:`~codestrata_platform.community_cloud_api.telemetry.enums.TelemetryClientName`'s
       members *and* must match the revalidated payload's ``client.name``.
    5. ``storage_object_invalid`` — the resolved
       :class:`~.objects.ImmutableRawStorageObject` (built via
       :func:`~.immutable_write.build_immutable_raw_storage_object`, then
       given the optional ``codestrata-client-type`` extra metadata) must
       itself validate.
    6. ``partition_invalid`` — the resolved object key and S3 metadata must
       match the partition policy's generic dimensions and metadata
       allowlist.

    Never calls a store — persistence is the caller's responsibility (see
    :func:`store_projected_telemetry`).
    """

    active_data_lake_policy = data_lake_policy or CommunityDataLakePolicy.default()
    active_partition_policy = partition_policy or default_telemetry_partition_policy()

    _require(envelope.event_stream == EventStream.TELEMETRY.value, "stream_mismatch")
    _require(
        envelope.envelope_schema_version
        in active_partition_policy.supported_envelope_schema_versions,
        "unsupported_envelope_schema",
    )
    _require(
        envelope.source_schema_version
        in active_partition_policy.supported_source_schema_versions,
        "unsupported_source_schema",
    )
    _require(
        envelope.source_policy_version in active_partition_policy.supported_source_policy_ids,
        "unsupported_source_policy",
    )

    try:
        request = TelemetryIngestionRequest.model_validate(dict(envelope.payload))
    except Exception as exc:  # pydantic ValidationError, or any shape mismatch
        raise PartitionProjectionError("invalid_payload") from exc

    client_type = envelope.client.client_type
    _require(client_type in _TELEMETRY_CLIENT_TYPES, "invalid_client_type")
    _require(client_type == request.client.name, "invalid_client_type")

    try:
        base_storage_object = build_immutable_raw_storage_object(
            envelope, active_data_lake_policy
        )
        storage_object = merge_extra_s3_metadata(
            base_storage_object,
            {CLIENT_TYPE_METADATA_KEY: client_type},
        )
    except Exception as exc:  # domain validation errors from immutable_write/objects
        raise PartitionProjectionError("storage_object_invalid") from exc

    try:
        assert_partition_key_matches_policy(
            storage_object.object_key, active_partition_policy, envelope
        )
        assert_s3_metadata_matches_policy(
            storage_object.to_s3_metadata(), active_partition_policy
        )
    except (StreamPartitionError, StorageObjectError) as exc:
        raise PartitionProjectionError("partition_invalid") from exc

    diagnostics = PartitionProjectionDiagnostics(
        event_stream=storage_object.event_stream,
        envelope_schema_version=storage_object.envelope_schema_version,
        source_schema_version=storage_object.source_schema_version,
        assessment_schema_version=None,
        client_type=client_type,
        partition_policy_version=active_partition_policy.policy_version,
        partition_valid=True,
        projection_status="projected",
        safe_event_reference=storage_object.safe_event_reference,
        safe_object_reference=(
            f"{STORED_OBJECT_REFERENCE_PREFIX}{storage_object.opaque_object_id_hex[:16]}"
        ),
        limitations=active_partition_policy.limitations,
    )
    return StorageProjectionResult(storage_object=storage_object, diagnostics=diagnostics)


def store_projected_telemetry(
    store: "CommunityDataLakeStore",
    projection: StorageProjectionResult,
) -> "StorageWriteResult":
    """Persist an already-projected :class:`~.stream_storage.StorageProjectionResult`.

    Requires ``store.put_immutable_storage_object`` — the only path that
    writes the *projected* object (including its ``codestrata-client-type``
    extra metadata) byte-exact, without rebuilding from the envelope. Both
    :class:`~.ports.InMemoryCommunityDataLakeStore` (Slice 8.2) and
    :class:`~.infrastructure.s3_store.CommunityDataLakeS3Store` (Slice 8.4)
    expose it. Raises :class:`AttributeError` for any store that does not —
    ``store.put_immutable_event(envelope)`` alone would silently rebuild the
    storage object from the envelope and drop the projector's extra
    metadata, which would be a durability defect, not a valid fallback.
    """

    # Slice 8.13: projected-object put is on the Protocol — do not fall back
    # to put_immutable_event (that rebuild drops stream-specific metadata).
    return store.put_immutable_storage_object(projection.storage_object)


__all__ = [
    "ALLOWED_PARTITION_PROJECTION_ERROR_CODES",
    "CLIENT_TYPE_METADATA_KEY",
    "PartitionProjectionError",
    "TELEMETRY_PARTITION_POLICY_ID",
    "TELEMETRY_PARTITION_POLICY_URN",
    "TELEMETRY_PARTITION_POLICY_VERSION",
    "default_telemetry_partition_policy",
    "project_telemetry_storage_object",
    "store_projected_telemetry",
]

"""CLI event stream partitioning: policy + storage-object projection (Slice 8.6).

Binds the generic Slice 8.4 partition-policy and diagnostics machinery
(:mod:`~codestrata_platform.community_cloud_api.data_lake.partition_policies`,
:mod:`~codestrata_platform.community_cloud_api.data_lake.stream_partitions`,
:mod:`~codestrata_platform.community_cloud_api.data_lake.partition_diagnostics`,
:mod:`~codestrata_platform.community_cloud_api.data_lake.stream_storage`) to
the third concrete stream: ``cli_event``. Nothing in this module (or
anything it imports) is called by ``app.py``, ``deployment/wiring.py``, the
CLI emitter, the telemetry runtime, or any endpoint service — see
``platform/tests/community_cloud_api/data_lake/test_cli_event_partition_boundary.py``.

## Partition dimension decision (Slice 8.6)

The accepted object key for this stream is the **generic Hive path only**,
identical in shape to ``assessment_metadata`` (Slice 8.4) and ``telemetry``
(Slice 8.5)::

    raw/stream=cli_event/schema_version=1.0/year=YYYY/month=MM/day=DD/{opaque}.json

No additional path dimension is added for ``operation``, ``lifecycle``,
``result``, ``failure_category``, ``client_type``, ``invocation_source``, or
any assessment-head field. Rationale:

- **Cross-stream path consistency.** Every stream registered so far
  (``assessment_metadata``, ``telemetry``, and now ``cli_event``) keeps the
  accepted path at exactly `stream=` / `schema_version=` / `year=` /
  `month=` / `day=`, so a future shared Glue/Athena catalog definition never
  needs a per-stream special case.
- **``operation`` is an analytics dimension whose catalog evolves.** The CLI
  operation catalog (see
  :mod:`~codestrata_platform.community_cloud_api.cli_events.catalog`) is
  explicitly versioned (``CLI_OPERATION_CATALOG_VERSION``) *because* it is
  expected to gain/rename/retire canonical operations over time. Baking
  ``operation`` into the physical storage path would force a partition
  layout migration every time the catalog changes — exactly the same
  reasoning Slice 8.5 applied to telemetry's ``event_type``.
- **``client_type`` (path dimension) is redundant for this stream.** Unlike
  ``telemetry``/``assessment_metadata``, which accept multiple client types,
  the ``cli_event`` stream's source contract allowlists exactly one client:
  ``codestrata_cli`` (see
  :data:`~codestrata_platform.community_cloud_api.cli_events.enums.CLI_CLIENT_NAME`).
  A path (or even metadata) dimension that always has exactly one value adds
  zero filtering power — see the S3 metadata decision below for why this
  extends to metadata too, not just the path.
- **``lifecycle``/``result``/``failure_category``/``invocation_source`` are
  all private-payload analytics fields**, not stable transport-classification
  concepts — none of them has a filtering consumer in this repository today,
  and several (``failure_category`` in particular) are effectively
  open-ended relative to the fixed five-dimension generic path.

## S3 metadata decision (Slice 8.6)

**No new S3 metadata key is added for this stream at all.** The
``cli_event`` partition policy's ``s3_metadata_allowlist`` is exactly
:data:`~codestrata_platform.community_cloud_api.data_lake.objects.BASE_S3_METADATA_KEYS`
— the five keys every :class:`~.objects.ImmutableRawStorageObject` always
carries — and nothing else. In particular:

- **No ``codestrata-client-type`` key.** Unlike the ``telemetry`` stream
  (Slice 8.5), where three client types made the metadata a useful coarse
  filter, the ``cli_event`` stream's client is always ``codestrata_cli`` —
  a constant value carries no information, so attaching it as metadata
  would be pure redundancy.
- **No ``codestrata-cli-operation`` (or similarly named) key.** Mirrors the
  path decision above: the operation catalog evolves, so it stays
  private-payload-only, never S3 metadata either.
- **No ``codestrata-cli-lifecycle`` / ``-result`` key.** Same reasoning —
  these are analytics dimensions belonging to future aggregate processing,
  not raw-object partitioning/metadata.

Because no extra metadata is ever attached, :func:`project_cli_event_storage_object`
never calls
:func:`~codestrata_platform.community_cloud_api.data_lake.stream_storage.merge_extra_s3_metadata`
— unlike the ``assessment_metadata`` and ``telemetry`` projectors, the base
object returned by
:func:`~codestrata_platform.community_cloud_api.data_lake.immutable_write.build_immutable_raw_storage_object`
*is* the final storage object for this stream.

## The new ``supported_operation_catalog_versions`` / ``operation_catalog_version`` fields

Slice 8.6 is the first stream to set
:attr:`~codestrata_platform.community_cloud_api.data_lake.partition_policies.StreamPartitionPolicy.supported_operation_catalog_versions`
to a non-empty value —
``frozenset({CLI_OPERATION_CATALOG_VERSION})`` (currently ``{"1.0"}``) — and
the first projector to set
:attr:`~codestrata_platform.community_cloud_api.data_lake.partition_diagnostics.PartitionProjectionDiagnostics.operation_catalog_version`.
This is a *catalog-version* check, not a per-event ``operation`` value
check: it confirms the projector is validating against the operation
catalog version the partition policy expects, independent of which
specific canonical operation (or alias) the submitted event used. The
per-event ``operation`` value itself is never surfaced here — it stays
private-payload-only, exactly like ``lifecycle``/``result`` (see the
dimension decision above).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from codestrata_platform.community_cloud_api.cli_events.catalog import (
    CLI_OPERATION_CATALOG_VERSION,
)
from codestrata_platform.community_cloud_api.cli_events.enums import CLI_CLIENT_NAME
from codestrata_platform.community_cloud_api.cli_events.models import CliEventRequest
from codestrata_platform.community_cloud_api.cli_events.policy import (
    COMMUNITY_CLI_EVENT_POLICY_URN,
    COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.enums import EventStream
from codestrata_platform.community_cloud_api.data_lake.envelopes import DataLakeEnvelope
from codestrata_platform.community_cloud_api.data_lake.immutable_write import (
    build_immutable_raw_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.objects import (
    BASE_S3_METADATA_KEYS,
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
)

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids a runtime import cycle
    from codestrata_platform.community_cloud_api.data_lake.ports import (
        CommunityDataLakeStore,
        StorageWriteResult,
    )

CLI_EVENT_PARTITION_POLICY_ID = "community-cli-event-partition-policy"
CLI_EVENT_PARTITION_POLICY_VERSION = "1.0"
CLI_EVENT_PARTITION_POLICY_URN = (
    f"{CLI_EVENT_PARTITION_POLICY_ID}:{CLI_EVENT_PARTITION_POLICY_VERSION}"
)

_SUPPORTED_ENVELOPE_SCHEMA_VERSIONS = frozenset({"1.0"})
_SUPPORTED_SOURCE_SCHEMA_VERSIONS = frozenset({COMMUNITY_CLI_EVENT_SCHEMA_VERSION})
_SUPPORTED_SOURCE_POLICY_IDS = frozenset({COMMUNITY_CLI_EVENT_POLICY_URN})
_SUPPORTED_OPERATION_CATALOG_VERSIONS = frozenset({CLI_OPERATION_CATALOG_VERSION})

# Field names that must never become a partition path dimension for this
# stream — enforced structurally by ``stream_partitions`` against the parsed
# Hive dimension names of any candidate key, independent of (and in addition
# to) the "generic dimensions only" decision above. Deliberately broad: it
# covers every approved-private CLI event field (endpoint + context blocks),
# the CLI policy's own ``FORBIDDEN_FIELD_NAMES``, plus a handful of
# cross-stream identity/shape fields already forbidden for the other two
# registered streams.
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
        "operation",
        "lifecycle",
        "result",
        "failure_category",
        "duration_bucket",
        "invocation_source",
        "execution_mode",
        "output_format",
        "offline_mode",
        "ai_requested",
        "selected_assessment_heads",
        "terminal_environment",
        "command",
        "command_line",
        "argv",
        "args",
        "arguments",
        "cwd",
        "working_directory",
        "repository",
        "repository_name",
        "repository_path",
        "repository_url",
        "path",
        "file",
        "file_path",
        "filename",
        "source",
        "source_code",
        "terminal",
        "terminal_history",
        "shell_history",
        "stdout",
        "stderr",
        "exception",
        "exception_message",
        "stack_trace",
        "language",
        "executed_heads",
        "assessment_status",
        "assessment_schema_version",
    }
)

_LIMITATIONS: tuple[str, ...] = (
    "no_extra_partition_dimensions_in_v0_2_0",
    "no_cli_specific_s3_metadata",
    "operation_remains_private_payload",
    "lifecycle_result_remain_private_payload",
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
        "unsupported_operation_catalog",
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


def default_cli_event_partition_policy() -> StreamPartitionPolicy:
    """The Slice 8.6 partition policy for the ``cli_event`` stream."""

    return StreamPartitionPolicy(
        policy_id=CLI_EVENT_PARTITION_POLICY_ID,
        policy_version=CLI_EVENT_PARTITION_POLICY_VERSION,
        event_stream=EventStream.CLI_EVENT,
        supported_envelope_schema_versions=_SUPPORTED_ENVELOPE_SCHEMA_VERSIONS,
        supported_source_schema_versions=_SUPPORTED_SOURCE_SCHEMA_VERSIONS,
        supported_source_policy_ids=_SUPPORTED_SOURCE_POLICY_IDS,
        supported_assessment_schema_versions=frozenset(),
        supported_operation_catalog_versions=_SUPPORTED_OPERATION_CATALOG_VERSIONS,
        s3_metadata_allowlist=frozenset(BASE_S3_METADATA_KEYS),
        forbidden_partition_fields=_FORBIDDEN_PARTITION_FIELDS,
        limitations=_LIMITATIONS,
    )


def _require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise PartitionProjectionError(code, detail)


def project_cli_event_storage_object(
    envelope: DataLakeEnvelope,
    *,
    data_lake_policy: CommunityDataLakePolicy | None = None,
    partition_policy: StreamPartitionPolicy | None = None,
) -> StorageProjectionResult:
    """Validate ``envelope`` and resolve it into a partition-checked storage object.

    Order of checks (every failure raises :class:`PartitionProjectionError`
    with a bounded, allowlisted code — see module-level constant):

    1. ``stream_mismatch`` — ``envelope.event_stream`` must be
       ``"cli_event"``.
    2. ``unsupported_envelope_schema`` / ``unsupported_source_schema`` /
       ``unsupported_source_policy`` — envelope/source identity must match
       the partition policy's supported sets.
    3. ``invalid_payload`` — ``payload`` must round-trip through
       :class:`CliEventRequest` (fail-closed typed re-check); this also
       rejects a corrupted/unsupported ``operation`` (or any
       command/argv/cwd-shaped extra field, which ``extra="forbid"``
       rejects outright), since the model's own field validator enforces
       the CLI operation catalog allowlist.
    4. ``invalid_client_type`` — ``envelope.client.client_type`` must equal
       :data:`~codestrata_platform.community_cloud_api.cli_events.enums.CLI_CLIENT_NAME`
       *and* must match the revalidated payload's ``client.name`` — both
       sides are checked independently so neither can be silently trusted
       alone.
    5. ``unsupported_operation_catalog`` —
       :data:`~codestrata_platform.community_cloud_api.cli_events.catalog.CLI_OPERATION_CATALOG_VERSION`
       must be one of the partition policy's
       ``supported_operation_catalog_versions``.
    6. ``storage_object_invalid`` — the resolved
       :class:`~.objects.ImmutableRawStorageObject` (built via
       :func:`~.immutable_write.build_immutable_raw_storage_object` alone —
       **no** extra S3 metadata is ever merged in for this stream, see
       module docstring) must itself validate.
    7. ``partition_invalid`` — the resolved object key and S3 metadata must
       match the partition policy's generic dimensions and metadata
       allowlist (exactly the five base keys for this stream).

    Never calls a store — persistence is the caller's responsibility (see
    :func:`store_projected_cli_event`).
    """

    active_data_lake_policy = data_lake_policy or CommunityDataLakePolicy.default()
    active_partition_policy = partition_policy or default_cli_event_partition_policy()

    _require(envelope.event_stream == EventStream.CLI_EVENT.value, "stream_mismatch")
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
        request = CliEventRequest.model_validate(dict(envelope.payload))
    except Exception as exc:  # pydantic ValidationError, or any shape mismatch
        raise PartitionProjectionError("invalid_payload") from exc

    client_type = envelope.client.client_type
    _require(client_type == CLI_CLIENT_NAME, "invalid_client_type")
    _require(client_type == request.client.name, "invalid_client_type")

    _require(
        CLI_OPERATION_CATALOG_VERSION
        in active_partition_policy.supported_operation_catalog_versions,
        "unsupported_operation_catalog",
    )

    try:
        storage_object = build_immutable_raw_storage_object(envelope, active_data_lake_policy)
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
        client_type=None,
        operation_catalog_version=CLI_OPERATION_CATALOG_VERSION,
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


def store_projected_cli_event(
    store: "CommunityDataLakeStore",
    projection: StorageProjectionResult,
) -> "StorageWriteResult":
    """Persist an already-projected :class:`~.stream_storage.StorageProjectionResult`.

    Requires ``store.put_immutable_storage_object`` — the only path that
    writes the *projected* object byte-exact, without rebuilding from the
    envelope. Both :class:`~.ports.InMemoryCommunityDataLakeStore`
    (Slice 8.2) and :class:`~.infrastructure.s3_store.CommunityDataLakeS3Store`
    (Slice 8.4) expose it. Raises :class:`AttributeError` for any store that
    does not — mirrors ``store_projected_telemetry`` /
    ``store_projected_assessment_metadata`` exactly, even though this
    stream's projection carries no extra metadata to lose: consistency
    across every stream's persistence helper matters more than this
    particular stream's fallback safety would.
    """

    # Slice 8.13: projected-object put is on the Protocol — do not fall back
    # to put_immutable_event (that rebuild drops stream-specific metadata).
    return store.put_immutable_storage_object(projection.storage_object)


__all__ = [
    "ALLOWED_PARTITION_PROJECTION_ERROR_CODES",
    "CLI_EVENT_PARTITION_POLICY_ID",
    "CLI_EVENT_PARTITION_POLICY_URN",
    "CLI_EVENT_PARTITION_POLICY_VERSION",
    "PartitionProjectionError",
    "default_cli_event_partition_policy",
    "project_cli_event_storage_object",
    "store_projected_cli_event",
]

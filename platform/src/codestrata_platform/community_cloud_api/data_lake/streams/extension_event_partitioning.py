"""Extension event stream partitioning: policy + storage-object projection (Slice 8.7).

Binds the generic Slice 8.4–8.6 partition-policy and diagnostics machinery
(:mod:`~codestrata_platform.community_cloud_api.data_lake.partition_policies`,
:mod:`~codestrata_platform.community_cloud_api.data_lake.stream_partitions`,
:mod:`~codestrata_platform.community_cloud_api.data_lake.partition_diagnostics`,
:mod:`~codestrata_platform.community_cloud_api.data_lake.stream_storage`) to
the fourth concrete stream: ``extension_event``. Nothing in this module (or
anything it imports) is called by ``app.py``, ``deployment/wiring.py``, the
VS Code extension emitters, the telemetry runtime, or any endpoint
service — see
``platform/tests/community_cloud_api/data_lake/test_extension_event_partition_boundary.py``.

## Partition dimension decision (Slice 8.7)

The accepted object key for this stream is the **generic Hive path only**,
identical in shape to ``assessment_metadata`` (8.4), ``telemetry`` (8.5),
and ``cli_event`` (8.6)::

    raw/stream=extension_event/schema_version=1.0/year=YYYY/month=MM/day=DD/{opaque}.json

No additional path dimension is added for ``client_type``, ``editor``,
``operation``, ``lifecycle``, ``result``, ``failure_category``,
``invocation_source``, workspace/report state, or assessment heads.
Rationale:

- **Cross-stream path consistency.** Every registered stream keeps the
  accepted path at exactly `stream=` / `schema_version=` / `year=` /
  `month=` / `day=`, so a future shared Glue/Athena catalog definition
  never needs a per-stream special case.
- **``operation`` is an analytics dimension whose catalog evolves.** The
  extension operation catalog (see
  :mod:`~codestrata_platform.community_cloud_api.extension_events.catalog`)
  is explicitly versioned because command IDs grow and rename over time.
  Baking ``operation`` into the physical storage path would force a
  partition-layout migration on every catalog change — the same reasoning
  Slice 8.5 applied to telemetry's ``event_type`` and Slice 8.6 applied to
  CLI operations.
- **``client_type`` / ``editor`` as path dimensions are unnecessary.** The
  active pair is one-to-one today (``vscode_extension``↔``vscode``). The
  retired historical pair (``cursor_extension``↔``cursor``) remains
  readable for previously accepted records (Slice 12.4) but is rejected by
  active projection. The value is already carried in S3 metadata (see
  below) and in the private payload.
- **``lifecycle`` / ``result`` / ``failure_category`` / context fields are
  private-payload analytics fields**, not stable transport-classification
  concepts.

## S3 metadata decision (Slice 8.7) — Option B

Exactly one stream-specific S3 metadata key is added:
``codestrata-client-type`` — the envelope's ``client.client_type`` value
(active allowlist :data:`~codestrata_platform.community_cloud_api.extension_events.enums.ALLOWED_EXTENSION_CLIENTS`:
``vscode_extension`` only; historical ``cursor_extension`` metadata remains
valid for inspection of existing objects — Slice 12.4), attached only by
:func:`project_extension_event_storage_object`.

This reuses the existing
:data:`~codestrata_platform.community_cloud_api.data_lake.objects.ALLOWED_S3_METADATA_KEYS`
key introduced for telemetry in Slice 8.5 — **no** synonym such as
``codestrata-extension-client`` or ``codestrata-editor`` is introduced.

Rationale for Option B (one bounded client-type metadata field) over
Option A (generic metadata only, as CLI chose in Slice 8.6):

- **Active first-party client.** Unlike ``cli_event`` (always
  ``codestrata_cli``), this stream's active emitter is VS Code only
  (``vscode_extension``). Retired ``cursor_extension`` is historical-only
  (Slice 12.4).
- **Editor is not duplicated.** Because the active client↔editor pair is
  authoritative and one-to-one, attaching both would be redundant. Editor
  remains private-payload-only; client type alone is the metadata signal.
- **Operation / lifecycle / context stay out of metadata.** Catalog
  evolution, analytics semantics, and privacy all argue against promoting
  them.

:func:`project_extension_event_storage_object` therefore calls
:func:`~codestrata_platform.community_cloud_api.data_lake.stream_storage.merge_extra_s3_metadata`
exactly once for ``codestrata-client-type``, mirroring telemetry — and
persistence **must** go through
:func:`store_projected_extension_event` /
``put_immutable_storage_object`` so that extra metadata is not dropped by
an envelope rebuild.

## Operation catalog version fields

Like Slice 8.6 CLI events, this stream sets
:attr:`~codestrata_platform.community_cloud_api.data_lake.partition_policies.StreamPartitionPolicy.supported_operation_catalog_versions`
to ``frozenset({EXTENSION_OPERATION_CATALOG_VERSION})`` and surfaces
:attr:`~codestrata_platform.community_cloud_api.data_lake.partition_diagnostics.PartitionProjectionDiagnostics.operation_catalog_version`.
This is a *catalog-version* check, not a per-event ``operation`` value
check: the per-event operation stays private-payload-only.
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
from codestrata_platform.community_cloud_api.extension_events.catalog import (
    EXTENSION_OPERATION_CATALOG_VERSION,
)
from codestrata_platform.community_cloud_api.extension_events.enums import (
    ALLOWED_EXTENSION_CLIENTS,
)
from codestrata_platform.community_cloud_api.extension_events.models import ExtensionEventRequest
from codestrata_platform.community_cloud_api.extension_events.policy import (
    COMMUNITY_EXTENSION_EVENT_POLICY_URN,
    COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
)

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids a runtime import cycle
    from codestrata_platform.community_cloud_api.data_lake.ports import (
        CommunityDataLakeStore,
        StorageWriteResult,
    )

EXTENSION_EVENT_PARTITION_POLICY_ID = "community-extension-event-partition-policy"
EXTENSION_EVENT_PARTITION_POLICY_VERSION = "1.0"
EXTENSION_EVENT_PARTITION_POLICY_URN = (
    f"{EXTENSION_EVENT_PARTITION_POLICY_ID}:{EXTENSION_EVENT_PARTITION_POLICY_VERSION}"
)

# Informational only — never part of the partition path (see module
# docstring). Optional on the resulting object: only
# ``project_extension_event_storage_object`` attaches it. Reuses the same
# key string as telemetry (Slice 8.5); do not introduce a synonym.
CLIENT_TYPE_METADATA_KEY = "codestrata-client-type"

_SUPPORTED_ENVELOPE_SCHEMA_VERSIONS = frozenset({"1.0"})
_SUPPORTED_SOURCE_SCHEMA_VERSIONS = frozenset({COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION})
_SUPPORTED_SOURCE_POLICY_IDS = frozenset({COMMUNITY_EXTENSION_EVENT_POLICY_URN})
_SUPPORTED_OPERATION_CATALOG_VERSIONS = frozenset({EXTENSION_OPERATION_CATALOG_VERSION})

_EXTENSION_CLIENT_TYPES: frozenset[str] = frozenset(ALLOWED_EXTENSION_CLIENTS)

# Field names that must never become a partition path dimension for this
# stream — enforced structurally by ``stream_partitions`` against the parsed
# Hive dimension names of any candidate key, independent of (and in addition
# to) the "generic dimensions only" decision above.
_FORBIDDEN_PARTITION_FIELDS: frozenset[str] = frozenset(
    {
        "event_id",
        "installation_id",
        "request_id",
        "ip",
        "ip_address",
        "client_type",
        "client_version",
        "editor",
        "editor_version",
        "platform",
        "operation",
        "lifecycle",
        "result",
        "failure_category",
        "duration_bucket",
        "invocation_source",
        "user_initiated",
        "offline_mode",
        "ai_requested",
        "selected_assessment_heads",
        "report_surface",
        "workspace_state",
        "workspace",
        "workspace_path",
        "workspace_name",
        "workspace_uri",
        "document",
        "document_path",
        "document_uri",
        "folder",
        "folder_path",
        "folder_uri",
        "active_file",
        "file",
        "file_path",
        "filename",
        "path",
        "command",
        "command_id",
        "command_line",
        "argv",
        "args",
        "arguments",
        "repository",
        "repository_name",
        "repository_path",
        "repository_url",
        "project",
        "project_name",
        "source",
        "source_code",
        "terminal",
        "terminal_text",
        "stdout",
        "stderr",
        "exception",
        "exception_message",
        "stack_trace",
        "error_message",
        "settings",
        "environment",
        "user",
        "account",
        "prompt",
        "response",
        "provider",
        "model",
        "cost",
        "language",
        "executed_heads",
        "assessment_status",
        "assessment_schema_version",
    }
)

_LIMITATIONS: tuple[str, ...] = (
    "no_extra_partition_dimensions_in_v0_2_0",
    "client_type_in_metadata_not_path",
    "editor_remains_private_payload",
    "operation_remains_private_payload",
    "lifecycle_result_remain_private_payload",
    "workspace_document_repository_excluded",
    "installation_id_private_payload_only",
    "no_store_wiring_this_module_only_projects",
)

# Bounded, allowlisted rejection codes for ``PartitionProjectionError``.
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


def default_extension_event_partition_policy() -> StreamPartitionPolicy:
    """The Slice 8.7 partition policy for the ``extension_event`` stream."""

    return StreamPartitionPolicy(
        policy_id=EXTENSION_EVENT_PARTITION_POLICY_ID,
        policy_version=EXTENSION_EVENT_PARTITION_POLICY_VERSION,
        event_stream=EventStream.EXTENSION_EVENT,
        supported_envelope_schema_versions=_SUPPORTED_ENVELOPE_SCHEMA_VERSIONS,
        supported_source_schema_versions=_SUPPORTED_SOURCE_SCHEMA_VERSIONS,
        supported_source_policy_ids=_SUPPORTED_SOURCE_POLICY_IDS,
        supported_assessment_schema_versions=frozenset(),
        supported_operation_catalog_versions=_SUPPORTED_OPERATION_CATALOG_VERSIONS,
        s3_metadata_allowlist=frozenset(ALLOWED_S3_METADATA_KEYS),
        forbidden_partition_fields=_FORBIDDEN_PARTITION_FIELDS,
        limitations=_LIMITATIONS,
    )


def _require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise PartitionProjectionError(code, detail)


def project_extension_event_storage_object(
    envelope: DataLakeEnvelope,
    *,
    data_lake_policy: CommunityDataLakePolicy | None = None,
    partition_policy: StreamPartitionPolicy | None = None,
) -> StorageProjectionResult:
    """Validate ``envelope`` and resolve it into a partition-checked storage object.

    Order of checks (every failure raises :class:`PartitionProjectionError`
    with a bounded, allowlisted code — see module-level constant):

    1. ``stream_mismatch`` — ``envelope.event_stream`` must be
       ``"extension_event"``.
    2. ``unsupported_envelope_schema`` / ``unsupported_source_schema`` /
       ``unsupported_source_policy`` — envelope/source identity must match
       the partition policy's supported sets.
    3. ``invalid_payload`` — ``payload`` must round-trip through
       :class:`ExtensionEventRequest` (fail-closed typed re-check); this
       also rejects unknown operations, client/editor pair mismatches,
       and workspace/document/path-shaped extras (``extra="forbid"`` plus
       the model's own validators).
    4. ``invalid_client_type`` — ``envelope.client.client_type`` must be one
       of :data:`~codestrata_platform.community_cloud_api.extension_events.enums.ALLOWED_EXTENSION_CLIENTS`
       *and* must match the revalidated payload's ``client.name``.
    5. ``unsupported_operation_catalog`` —
       :data:`~codestrata_platform.community_cloud_api.extension_events.catalog.EXTENSION_OPERATION_CATALOG_VERSION`
       must be one of the partition policy's
       ``supported_operation_catalog_versions``.
    6. ``storage_object_invalid`` — the resolved
       :class:`~.objects.ImmutableRawStorageObject` (built via
       :func:`~.immutable_write.build_immutable_raw_storage_object`, then
       given the optional ``codestrata-client-type`` extra metadata) must
       itself validate.
    7. ``partition_invalid`` — the resolved object key and S3 metadata must
       match the partition policy's generic dimensions and metadata
       allowlist.

    Never calls a store — persistence is the caller's responsibility (see
    :func:`store_projected_extension_event`).
    """

    active_data_lake_policy = data_lake_policy or CommunityDataLakePolicy.default()
    active_partition_policy = partition_policy or default_extension_event_partition_policy()

    _require(envelope.event_stream == EventStream.EXTENSION_EVENT.value, "stream_mismatch")
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
        request = ExtensionEventRequest.model_validate(dict(envelope.payload))
    except Exception as exc:  # pydantic ValidationError, or any shape mismatch
        raise PartitionProjectionError("invalid_payload") from exc

    client_type = envelope.client.client_type
    _require(client_type in _EXTENSION_CLIENT_TYPES, "invalid_client_type")
    _require(client_type == request.client.name, "invalid_client_type")

    _require(
        EXTENSION_OPERATION_CATALOG_VERSION
        in active_partition_policy.supported_operation_catalog_versions,
        "unsupported_operation_catalog",
    )

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
        operation_catalog_version=EXTENSION_OPERATION_CATALOG_VERSION,
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


def store_projected_extension_event(
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
    metadata.
    """

    # Slice 8.13: projected-object put is on the Protocol — do not fall back
    # to put_immutable_event (that rebuild drops stream-specific metadata).
    return store.put_immutable_storage_object(projection.storage_object)


__all__ = [
    "ALLOWED_PARTITION_PROJECTION_ERROR_CODES",
    "CLIENT_TYPE_METADATA_KEY",
    "EXTENSION_EVENT_PARTITION_POLICY_ID",
    "EXTENSION_EVENT_PARTITION_POLICY_URN",
    "EXTENSION_EVENT_PARTITION_POLICY_VERSION",
    "PartitionProjectionError",
    "default_extension_event_partition_policy",
    "project_extension_event_storage_object",
    "store_projected_extension_event",
]

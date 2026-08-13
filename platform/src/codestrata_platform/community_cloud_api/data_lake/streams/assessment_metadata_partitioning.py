"""Assessment metadata stream partitioning: policy + storage-object projection (Slice 8.4).

Binds the generic Slice 8.4 partition-policy and diagnostics machinery
(:mod:`~codestrata_platform.community_cloud_api.data_lake.partition_policies`,
:mod:`~codestrata_platform.community_cloud_api.data_lake.stream_partitions`,
:mod:`~codestrata_platform.community_cloud_api.data_lake.partition_diagnostics`,
:mod:`~codestrata_platform.community_cloud_api.data_lake.stream_storage`) to
the one concrete stream this slice covers: ``assessment_metadata``. Nothing
in this module (or anything it imports) is called by ``app.py``,
``deployment/wiring.py``, or any endpoint service — see
``platform/tests/community_cloud_api/data_lake/test_assessment_metadata_partition_boundary.py``.

## Partition dimension decision (Slice 8.4)

The accepted object key for this stream is the **generic Hive path only**::

    raw/stream=assessment_metadata/schema_version=1.0/year=YYYY/month=MM/day=DD/{opaque}.json

No additional path dimension is added for ``client_type``,
``assessment_status``, ``execution_result``, ``assessment_schema_version``,
``language``, ``executed_heads``, or ``repository_shape``. Rationale:

- **Low operational need.** No analytics/Athena/dashboard consumer exists in
  this repository yet that would benefit from a finer-grained partition on
  any of these fields.
- **Avoid cardinality blow-up.** Several candidates
  (``executed_heads`` combinations, ``primary_language``,
  ``repository_shape``) are effectively unbounded or high-cardinality
  relative to the fixed five-dimension generic path every other stream
  already uses — adding them would multiply the number of S3 prefixes
  without a corresponding reader.
- **Cross-stream path consistency.** Keeping every stream's accepted path at
  exactly `stream=` / `schema_version=` / `year=` / `month=` / `day=`
  simplifies any future shared Glue/Athena catalog definition across all
  five streams.
- **Avoid identity fingerprinting.** Low-cardinality-per-repository
  attributes (language, shape, executed-head combination) become more
  re-identifying once combined with acceptance date and per-prefix object
  count. Keeping them private-payload-only (never in the key) avoids this
  risk entirely; see ``forbidden_partition_fields`` below for the explicit,
  enforced list.

The Engine assessment report contract version (``assessment_schema_version``,
currently ``"1.2"``) is instead surfaced as an **optional S3 metadata key**
(``codestrata-assessment-schema``) — informational only, never part of the
partition path — validated against the same allowlist the endpoint contract
already enforces
(:data:`~codestrata_platform.community_cloud_api.assessment_metadata.policy.ALLOWED_ASSESSMENT_SCHEMA_VERSIONS`).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentMetadataRequest,
)
from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
    ALLOWED_ASSESSMENT_SCHEMA_VERSIONS,
)
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

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids a runtime import cycle
    from codestrata_platform.community_cloud_api.data_lake.ports import (
        CommunityDataLakeStore,
        StorageWriteResult,
    )

ASSESSMENT_METADATA_PARTITION_POLICY_ID = "community-assessment-metadata-partition-policy"
ASSESSMENT_METADATA_PARTITION_POLICY_VERSION = "1.0"
ASSESSMENT_METADATA_PARTITION_POLICY_URN = (
    f"{ASSESSMENT_METADATA_PARTITION_POLICY_ID}:{ASSESSMENT_METADATA_PARTITION_POLICY_VERSION}"
)

# Informational only — never part of the partition path (see module
# docstring for the dimension decision). Optional on the resulting object:
# only ``project_assessment_metadata_storage_object`` attaches it.
ASSESSMENT_SCHEMA_METADATA_KEY = "codestrata-assessment-schema"

_SUPPORTED_ENVELOPE_SCHEMA_VERSIONS = frozenset({"1.0"})
_SUPPORTED_SOURCE_SCHEMA_VERSIONS = frozenset({"1.0", "1.1"})
_SUPPORTED_SOURCE_POLICY_IDS = frozenset(
    {
        "community-assessment-metadata-policy:1.0",
    }
)
# Field names that must never become a partition path dimension for this
# stream — enforced structurally by ``stream_partitions`` against the parsed
# Hive dimension names of any candidate key, independent of (and in addition
# to) the "generic dimensions only" decision above.
_FORBIDDEN_PARTITION_FIELDS: frozenset[str] = frozenset(
    {
        "event_id",
        "installation_id",
        "repository_name",
        "repository_url",
        "language",
        "primary_language",
        "repository_shape",
        "executed_heads",
        "finding_count",
        "client_type",
        "assessment_status",
        "assessment_mode",
        "assessment_schema_version",
        "result",
        "duration_bucket",
    }
)

_LIMITATIONS: tuple[str, ...] = (
    "no_extra_partition_dimensions_in_v0_2_0",
    "assessment_schema_in_metadata_not_path",
    "heads_language_shape_remain_private_payload",
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
        "unsupported_assessment_schema",
        "missing_assessment_schema",
        "invalid_payload",
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


def default_assessment_metadata_partition_policy() -> StreamPartitionPolicy:
    """The Slice 8.4 partition policy for the ``assessment_metadata`` stream."""

    return StreamPartitionPolicy(
        policy_id=ASSESSMENT_METADATA_PARTITION_POLICY_ID,
        policy_version=ASSESSMENT_METADATA_PARTITION_POLICY_VERSION,
        event_stream=EventStream.ASSESSMENT_METADATA,
        supported_envelope_schema_versions=_SUPPORTED_ENVELOPE_SCHEMA_VERSIONS,
        supported_source_schema_versions=_SUPPORTED_SOURCE_SCHEMA_VERSIONS,
        supported_source_policy_ids=_SUPPORTED_SOURCE_POLICY_IDS,
        supported_assessment_schema_versions=frozenset(ALLOWED_ASSESSMENT_SCHEMA_VERSIONS),
        s3_metadata_allowlist=frozenset(ALLOWED_S3_METADATA_KEYS),
        forbidden_partition_fields=_FORBIDDEN_PARTITION_FIELDS,
        limitations=_LIMITATIONS,
    )


def extract_assessment_schema_version(envelope: DataLakeEnvelope) -> str:
    """Return ``envelope.payload["assessment"]["assessment_schema_version"]``.

    Raises :class:`PartitionProjectionError` — ``invalid_payload`` if the
    ``assessment`` block itself is missing/malformed, ``missing_assessment_schema``
    if the field is absent or not a non-blank string. Never echoes the
    payload in either error.
    """

    assessment_block = (
        envelope.payload.get("assessment") if isinstance(envelope.payload, Mapping) else None
    )
    if not isinstance(assessment_block, Mapping):
        raise PartitionProjectionError("invalid_payload", "assessment_block_missing")
    version = assessment_block.get("assessment_schema_version")
    if not isinstance(version, str) or not version.strip():
        raise PartitionProjectionError("missing_assessment_schema")
    return version.strip()


def _require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise PartitionProjectionError(code, detail)


def project_assessment_metadata_storage_object(
    envelope: DataLakeEnvelope,
    *,
    data_lake_policy: CommunityDataLakePolicy | None = None,
    partition_policy: StreamPartitionPolicy | None = None,
) -> StorageProjectionResult:
    """Validate ``envelope`` and resolve it into a partition-checked storage object.

    Order of checks (every failure raises :class:`PartitionProjectionError`
    with a bounded, allowlisted code — see module-level constant):

    1. ``stream_mismatch`` — ``envelope.event_stream`` must be
       ``"assessment_metadata"``.
    2. ``unsupported_envelope_schema`` / ``unsupported_source_schema`` /
       ``unsupported_source_policy`` — envelope/source identity must match
       the partition policy's supported sets.
    3. ``missing_assessment_schema`` / ``unsupported_assessment_schema`` —
       ``payload["assessment"]["assessment_schema_version"]`` must be
       present and allowlisted.
    4. ``invalid_payload`` — ``payload`` must still round-trip through
       :class:`AssessmentMetadataRequest` (fail-closed typed re-check).
    5. ``storage_object_invalid`` — the resolved
       :class:`~.objects.ImmutableRawStorageObject` (built via
       :func:`~.immutable_write.build_immutable_raw_storage_object`, then
       given the optional ``codestrata-assessment-schema`` extra metadata)
       must itself validate.
    6. ``partition_invalid`` — the resolved object key and S3 metadata must
       match the partition policy's generic dimensions and metadata
       allowlist.

    Never calls a store — persistence is the caller's responsibility (see
    :func:`store_projected_assessment_metadata`).
    """

    active_data_lake_policy = data_lake_policy or CommunityDataLakePolicy.default()
    active_partition_policy = partition_policy or default_assessment_metadata_partition_policy()

    _require(envelope.event_stream == EventStream.ASSESSMENT_METADATA.value, "stream_mismatch")
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

    assessment_schema_version = extract_assessment_schema_version(envelope)
    _require(
        assessment_schema_version
        in active_partition_policy.supported_assessment_schema_versions,
        "unsupported_assessment_schema",
    )

    try:
        AssessmentMetadataRequest.model_validate(dict(envelope.payload))
    except Exception as exc:  # pydantic ValidationError, or any shape mismatch
        raise PartitionProjectionError("invalid_payload") from exc

    try:
        base_storage_object = build_immutable_raw_storage_object(
            envelope, active_data_lake_policy
        )
        storage_object = merge_extra_s3_metadata(
            base_storage_object,
            {ASSESSMENT_SCHEMA_METADATA_KEY: assessment_schema_version},
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
        assessment_schema_version=assessment_schema_version,
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


def store_projected_assessment_metadata(
    store: "CommunityDataLakeStore",
    projection: StorageProjectionResult,
) -> "StorageWriteResult":
    """Persist an already-projected :class:`~.stream_storage.StorageProjectionResult`.

    Requires ``store.put_immutable_storage_object`` — the only path that
    writes the *projected* object (including its
    ``codestrata-assessment-schema`` extra metadata) byte-exact, without
    rebuilding from the envelope. Both
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
    "ASSESSMENT_METADATA_PARTITION_POLICY_ID",
    "ASSESSMENT_METADATA_PARTITION_POLICY_URN",
    "ASSESSMENT_METADATA_PARTITION_POLICY_VERSION",
    "ASSESSMENT_SCHEMA_METADATA_KEY",
    "PartitionProjectionError",
    "default_assessment_metadata_partition_policy",
    "extract_assessment_schema_version",
    "project_assessment_metadata_storage_object",
    "store_projected_assessment_metadata",
]

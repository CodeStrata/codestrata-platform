"""AI usage stream partitioning: policy + storage-object projection (Slice 8.8).

Binds the generic Slice 8.4–8.7 partition-policy and diagnostics machinery
(:mod:`~codestrata_platform.community_cloud_api.data_lake.partition_policies`,
:mod:`~codestrata_platform.community_cloud_api.data_lake.stream_partitions`,
:mod:`~codestrata_platform.community_cloud_api.data_lake.partition_diagnostics`,
:mod:`~codestrata_platform.community_cloud_api.data_lake.stream_storage`) to
the fifth concrete stream: ``ai_usage``. Nothing in this module (or anything
it imports) is called by ``app.py``, ``deployment/wiring.py``, Engine AI
providers, client emitters, or any endpoint service — see
``platform/tests/community_cloud_api/data_lake/test_ai_usage_partition_boundary.py``.

## Partition dimension decision (Slice 8.8)

The accepted object key for this stream is the **generic Hive path only**,
identical in shape to every prior registered stream::

    raw/stream=ai_usage/schema_version=1.0/year=YYYY/month=MM/day=DD/{opaque}.json

No additional path dimension is added for ``client_type``, ``capability``,
``provider_ownership``, ``provider_family``, ``model_family``, ``outcome``,
``failure_category``, token/duration buckets, tool/RAG/graph usage, data
scope, or output usage. Rationale:

- **Cross-stream path consistency.** Every registered stream keeps the
  accepted path at exactly `stream=` / `schema_version=` / `year=` /
  `month=` / `day=`.
- **Capability / provider / model are analytics dimensions whose catalogs
  evolve.** Baking them into the physical storage path would force a
  partition-layout migration on every catalog change — the same reasoning
  prior slices applied to telemetry ``event_type`` and CLI/extension
  ``operation``.
- **Outcome / buckets / tool-RAG-graph enums are private-payload analytics
  fields**, not stable transport-classification concepts.

## S3 metadata decision (Slice 8.8) — Option B

Exactly one stream-specific S3 metadata key is added:
``codestrata-client-type`` — the envelope's ``client.client_type`` value
(one of :data:`~codestrata_platform.community_cloud_api.ai_usage.enums.ALLOWED_AI_USAGE_CLIENTS`:
``codestrata_cli``, ``vscode_extension``, or ``cursor_extension``),
attached only by :func:`project_ai_usage_storage_object`.

This reuses the existing key introduced for telemetry in Slice 8.5 —
**no** synonym is introduced, and **no** capability/provider/model/
outcome field is ever promoted to metadata.

Rationale for Option B over Option A (generic metadata only):

- **Three first-party clients.** Coarse operational separation of CLI /
  VS Code / Cursor objects mirrors telemetry and extension events.
- **AI product semantics stay private.** Capability, provider family,
  model family, and outcome remain encrypted payload only.

## Catalog version fields

Slice 8.8 is the first stream to set the three AI-specific
:class:`~.partition_policies.StreamPartitionPolicy` fields
``supported_capability_catalog_versions``,
``supported_provider_catalog_versions``, and
``supported_model_catalog_versions``, and the first projector to surface
the matching diagnostics scalars. They are kept *separate* so each catalog
can evolve independently (collapsing them into one frozenset would be a
compatibility defect because all three currently share the bare version
string ``"1.0"``). ``supported_operation_catalog_versions`` stays empty
for this stream.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from codestrata_platform.community_cloud_api.ai_usage.catalog import (
    AI_CAPABILITY_CATALOG_VERSION,
    AI_MODEL_FAMILY_CATALOG_VERSION,
    AI_PROVIDER_FAMILY_CATALOG_VERSION,
)
from codestrata_platform.community_cloud_api.ai_usage.enums import ALLOWED_AI_USAGE_CLIENTS
from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest
from codestrata_platform.community_cloud_api.ai_usage.policy import (
    COMMUNITY_AI_USAGE_POLICY_URN,
    COMMUNITY_AI_USAGE_SCHEMA_VERSION,
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

AI_USAGE_PARTITION_POLICY_ID = "community-ai-usage-partition-policy"
AI_USAGE_PARTITION_POLICY_VERSION = "1.0"
AI_USAGE_PARTITION_POLICY_URN = (
    f"{AI_USAGE_PARTITION_POLICY_ID}:{AI_USAGE_PARTITION_POLICY_VERSION}"
)

# Informational only — never part of the partition path. Reuses the same
# key string as telemetry/extension; do not introduce a synonym.
CLIENT_TYPE_METADATA_KEY = "codestrata-client-type"

_SUPPORTED_ENVELOPE_SCHEMA_VERSIONS = frozenset({"1.0"})
_SUPPORTED_SOURCE_SCHEMA_VERSIONS = frozenset({COMMUNITY_AI_USAGE_SCHEMA_VERSION})
_SUPPORTED_SOURCE_POLICY_IDS = frozenset({COMMUNITY_AI_USAGE_POLICY_URN})
_SUPPORTED_CAPABILITY_CATALOG_VERSIONS = frozenset({AI_CAPABILITY_CATALOG_VERSION})
_SUPPORTED_PROVIDER_CATALOG_VERSIONS = frozenset({AI_PROVIDER_FAMILY_CATALOG_VERSION})
_SUPPORTED_MODEL_CATALOG_VERSIONS = frozenset({AI_MODEL_FAMILY_CATALOG_VERSION})

_AI_USAGE_CLIENT_TYPES: frozenset[str] = frozenset(ALLOWED_AI_USAGE_CLIENTS)

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
        "capability",
        "execution_mode",
        "provider_ownership",
        "provider_family",
        "model_family",
        "model",
        "model_id",
        "outcome",
        "failure_category",
        "duration_bucket",
        "input_token_bucket",
        "output_token_bucket",
        "total_token_bucket",
        "token_count",
        "exact_tokens",
        "cost",
        "tool_usage",
        "rag_usage",
        "graph_usage",
        "output_usage",
        "data_scope",
        "assessment_head",
        "invocation_source",
        "prompt",
        "system_prompt",
        "user_prompt",
        "response",
        "completion",
        "generated_text",
        "source",
        "source_code",
        "source_context",
        "snippet",
        "chunk",
        "document",
        "repository",
        "repository_name",
        "repository_url",
        "project",
        "path",
        "file",
        "file_path",
        "embedding",
        "vector",
        "graph",
        "tool_payload",
        "headers",
        "provider_url",
        "api_key",
        "token",
        "secret",
        "credential",
        "authorization",
        "connection_string",
        "exception",
        "stack_trace",
        "error_message",
    }
)

_LIMITATIONS: tuple[str, ...] = (
    "no_extra_partition_dimensions_in_v0_2_0",
    "client_type_in_metadata_not_path",
    "capability_provider_model_remain_private_payload",
    "outcome_buckets_remain_private_payload",
    "tool_rag_graph_remain_private_payload",
    "prompt_response_source_excluded",
    "exact_token_cost_excluded",
    "installation_id_private_payload_only",
    "no_store_wiring_this_module_only_projects",
    "no_openrouter_support",
)

ALLOWED_PARTITION_PROJECTION_ERROR_CODES: frozenset[str] = frozenset(
    {
        "stream_mismatch",
        "unsupported_envelope_schema",
        "unsupported_source_schema",
        "unsupported_source_policy",
        "unsupported_capability_catalog",
        "unsupported_provider_catalog",
        "unsupported_model_catalog",
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


def default_ai_usage_partition_policy() -> StreamPartitionPolicy:
    """The Slice 8.8 partition policy for the ``ai_usage`` stream."""

    return StreamPartitionPolicy(
        policy_id=AI_USAGE_PARTITION_POLICY_ID,
        policy_version=AI_USAGE_PARTITION_POLICY_VERSION,
        event_stream=EventStream.AI_USAGE,
        supported_envelope_schema_versions=_SUPPORTED_ENVELOPE_SCHEMA_VERSIONS,
        supported_source_schema_versions=_SUPPORTED_SOURCE_SCHEMA_VERSIONS,
        supported_source_policy_ids=_SUPPORTED_SOURCE_POLICY_IDS,
        supported_assessment_schema_versions=frozenset(),
        supported_operation_catalog_versions=frozenset(),
        supported_capability_catalog_versions=_SUPPORTED_CAPABILITY_CATALOG_VERSIONS,
        supported_provider_catalog_versions=_SUPPORTED_PROVIDER_CATALOG_VERSIONS,
        supported_model_catalog_versions=_SUPPORTED_MODEL_CATALOG_VERSIONS,
        s3_metadata_allowlist=frozenset(ALLOWED_S3_METADATA_KEYS),
        forbidden_partition_fields=_FORBIDDEN_PARTITION_FIELDS,
        limitations=_LIMITATIONS,
    )


def _require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise PartitionProjectionError(code, detail)


def project_ai_usage_storage_object(
    envelope: DataLakeEnvelope,
    *,
    data_lake_policy: CommunityDataLakePolicy | None = None,
    partition_policy: StreamPartitionPolicy | None = None,
) -> StorageProjectionResult:
    """Validate ``envelope`` and resolve it into a partition-checked storage object.

    Order of checks (every failure raises :class:`PartitionProjectionError`
    with a bounded, allowlisted code):

    1. ``stream_mismatch`` — ``envelope.event_stream`` must be ``"ai_usage"``.
    2. ``unsupported_envelope_schema`` / ``unsupported_source_schema`` /
       ``unsupported_source_policy`` — envelope/source identity must match
       the partition policy's supported sets.
    3. ``invalid_payload`` — ``payload`` must round-trip through
       :class:`AiUsageRequest` (fail-closed typed re-check); this also
       rejects unknown capabilities/providers/models, prompt/response/
       source-shaped extras, and inconsistent token/failure rules.
    4. ``invalid_client_type`` — ``envelope.client.client_type`` must be one
       of :data:`~codestrata_platform.community_cloud_api.ai_usage.enums.ALLOWED_AI_USAGE_CLIENTS`
       *and* must match the revalidated payload's ``client.name``.
    5. ``unsupported_capability_catalog`` /
       ``unsupported_provider_catalog`` /
       ``unsupported_model_catalog`` — each AI catalog version must be in
       the matching partition-policy supported set.
    6. ``storage_object_invalid`` — the resolved
       :class:`~.objects.ImmutableRawStorageObject` (base object plus
       ``codestrata-client-type`` extra metadata) must itself validate.
    7. ``partition_invalid`` — the resolved object key and S3 metadata must
       match the partition policy.

    Never calls a store — persistence is the caller's responsibility (see
    :func:`store_projected_ai_usage`).
    """

    active_data_lake_policy = data_lake_policy or CommunityDataLakePolicy.default()
    active_partition_policy = partition_policy or default_ai_usage_partition_policy()

    _require(envelope.event_stream == EventStream.AI_USAGE.value, "stream_mismatch")
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
        request = AiUsageRequest.model_validate(dict(envelope.payload))
    except Exception as exc:  # pydantic ValidationError, or any shape mismatch
        raise PartitionProjectionError("invalid_payload") from exc

    client_type = envelope.client.client_type
    _require(client_type in _AI_USAGE_CLIENT_TYPES, "invalid_client_type")
    _require(client_type == request.client.name, "invalid_client_type")

    _require(
        AI_CAPABILITY_CATALOG_VERSION
        in active_partition_policy.supported_capability_catalog_versions,
        "unsupported_capability_catalog",
    )
    _require(
        AI_PROVIDER_FAMILY_CATALOG_VERSION
        in active_partition_policy.supported_provider_catalog_versions,
        "unsupported_provider_catalog",
    )
    _require(
        AI_MODEL_FAMILY_CATALOG_VERSION
        in active_partition_policy.supported_model_catalog_versions,
        "unsupported_model_catalog",
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
        operation_catalog_version=None,
        capability_catalog_version=AI_CAPABILITY_CATALOG_VERSION,
        provider_catalog_version=AI_PROVIDER_FAMILY_CATALOG_VERSION,
        model_catalog_version=AI_MODEL_FAMILY_CATALOG_VERSION,
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


def store_projected_ai_usage(
    store: "CommunityDataLakeStore",
    projection: StorageProjectionResult,
) -> "StorageWriteResult":
    """Persist an already-projected :class:`~.stream_storage.StorageProjectionResult`.

    Requires ``store.put_immutable_storage_object`` — the only path that
    writes the *projected* object (including its ``codestrata-client-type``
    extra metadata) byte-exact, without rebuilding from the envelope.
    """

    # Slice 8.13: projected-object put is on the Protocol — do not fall back
    # to put_immutable_event (that rebuild drops stream-specific metadata).
    return store.put_immutable_storage_object(projection.storage_object)


__all__ = [
    "ALLOWED_PARTITION_PROJECTION_ERROR_CODES",
    "AI_USAGE_PARTITION_POLICY_ID",
    "AI_USAGE_PARTITION_POLICY_URN",
    "AI_USAGE_PARTITION_POLICY_VERSION",
    "CLIENT_TYPE_METADATA_KEY",
    "PartitionProjectionError",
    "default_ai_usage_partition_policy",
    "project_ai_usage_storage_object",
    "store_projected_ai_usage",
]

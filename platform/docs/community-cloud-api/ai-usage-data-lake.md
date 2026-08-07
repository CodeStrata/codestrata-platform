# AI Usage Partitioning (Slice 8.8)

Slice 8.8 gives the `ai_usage` event stream its own versioned
**partition policy** and a stream-specific **storage-object projector**,
built on top of the Slice 8.1–8.7 Community Data Lake foundation and
reusing the exact same generic (stream-agnostic) partitioning machinery
[Slice 8.4](./assessment-metadata-data-lake.md) introduced for
`assessment_metadata`, [Slice 8.5](./telemetry-data-lake.md) reused for
`telemetry`, [Slice 8.6](./cli-event-data-lake.md) reused for
`cli_event`, and [Slice 8.7](./extension-event-data-lake.md) reused for
`extension_event`.

See [data-lake.md](./data-lake.md) (Slice 8.1 foundation),
[immutable-raw-storage.md](./immutable-raw-storage.md) (Slice 8.2 storage
contract), [data-lake-event-envelope.md](./data-lake-event-envelope.md)
(Slice 8.3 envelope/registry), and the Slice 8.4–8.7 stream docs for what
this slice builds on.

## What this slice does NOT do

- **Does not wire any endpoint to S3.** `app.py`, `deployment/wiring.py`,
  `deployment/settings.py`, the AI usage endpoint's own
  `routes.py`/`service.py`/`ports.py`, Engine AI providers, and client
  emitters are all unchanged — see
  `platform/tests/community_cloud_api/data_lake/test_ai_usage_partition_boundary.py`.
- **Does not start Slice 8.9.** No endpoint → storage wiring, durable
  event-identity store, Glue/Athena consumer, or quarantine pipeline is
  introduced here.
- **Does not bump any schema version.** Envelope schema and the AI usage
  endpoint schema both stay `1.0`. The capability / provider / model
  catalogs also stay `1.0`. Only the **new** partition policy is
  versioned, at `1.0`.
- **Does not change emitters or Engine AI.** No CLI, VS Code, Cursor, or
  Engine AI-provider change accompanies this slice.
- **Does not claim AI usage collection is operational.** The endpoint and
  sinks remain fail-closed / in-memory in production; this slice only adds
  an unwired projector.
- **Does not commit, plan, or apply any OpenTofu change.**
- **Does not add a durable event-identity/deduplication store.**
- **Does not add OpenRouter support.**

## Partition dimension decision

**Decision: retain the generic Hive path only** — identical in shape to every
prior registered stream:

```text
raw/stream=ai_usage/schema_version=1.0/year=YYYY/month=MM/day=DD/{opaque}.json
```

No dimension is added for `client_type`, `capability`,
`provider_ownership`, `provider_family`, `model_family`, `outcome`,
`failure_category`, token/duration buckets, tool/RAG/graph usage, data
scope, or output usage. Rationale:

- **Cross-stream path consistency.** Every registered stream keeps the
  accepted path at exactly `stream=` / `schema_version=` / `year=` /
  `month=` / `day=` — a fifth stream reusing the identical shape keeps any
  future shared Glue/Athena catalog definition simple.
- **Capability / provider / model are analytics dimensions whose catalogs
  evolve.** Baking them into the physical storage path would force a
  partition-layout migration on every catalog change — the same reasoning
  prior slices applied to telemetry `event_type` and CLI/extension
  `operation`.
- **Outcome / buckets / tool-RAG-graph enums are private-payload analytics
  fields**, not stable transport-classification concepts.

## S3 metadata decision (Option B)

**Decision: one bounded stream-specific S3 metadata key —
`codestrata-client-type`.** This reuses the existing
`ALLOWED_S3_METADATA_KEYS` entry introduced for telemetry in Slice 8.5 —
**no** synonym such as `codestrata-ai-client` or
`codestrata-capability` is introduced.

| Candidate | Disposition | Rationale |
| --- | --- | --- |
| `client.name` (→ `client_type`) | **S3 metadata** (`codestrata-client-type`) | Active clients (`codestrata_cli` / `vscode_extension`); historical `cursor_extension` metadata remains valid for inspection of existing objects (Slice 12.4) |
| `usage.capability` | Private payload only | Analytics vocabulary tied to the versioned, evolving capability catalog |
| `usage.provider_family` / `usage.model_family` | Private payload only | Analytics vocabulary tied to evolving provider/model catalogs |
| `usage.outcome` / buckets / tool-RAG-graph | Private payload only | Analytics/outcome fields belonging to future aggregate processing |
| `prompt` / `response` / exact cost / raw model id | Rejected at the endpoint | Never accepted; never in key/metadata/diagnostics |
| `event_id` | Private payload only | Approved endpoint field; never in key/metadata/diagnostics |
| `installation_id` | Private payload only | Approved endpoint field; optional, still never in key/metadata/diagnostics |

Rationale for Option B over Option A (generic metadata only, as CLI chose
in Slice 8.6): unlike `cli_event` (always `codestrata_cli`), this stream
separates active CLI / VS Code client-type objects. Retired historical
`cursor_extension` metadata on existing objects remains valid for inspection
(Slice 12.4 Approach A); active projection does not emit Cursor metadata.

`project_ai_usage_storage_object` therefore calls
`merge_extra_s3_metadata` exactly once for `codestrata-client-type`, and
persistence **must** go through `store_projected_ai_usage` /
`put_immutable_storage_object` so that extra metadata is not dropped by an
envelope rebuild.

## Catalog version fields

Slice 8.8 is the first stream to set the three AI-specific
`StreamPartitionPolicy` fields
`supported_capability_catalog_versions`,
`supported_provider_catalog_versions`, and
`supported_model_catalog_versions`, and the first projector to surface the
matching diagnostics scalars. They are kept **separate** so each catalog
can evolve independently (collapsing them into one frozenset would be a
compatibility defect because all three currently share the bare version
string `"1.0"`). `supported_operation_catalog_versions` stays empty for
this stream.

## The AI usage partition policy

```python
from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    default_ai_usage_partition_policy,
)

policy = default_ai_usage_partition_policy()
policy.policy_token  # "community-ai-usage-partition-policy:1.0"
```

| Field | Value |
| --- | --- |
| `policy_id` | `community-ai-usage-partition-policy` |
| `policy_version` | `1.0` |
| `event_stream` | `ai_usage` |
| `supported_envelope_schema_versions` | `{"1.0"}` |
| `supported_source_schema_versions` | `{"1.0"}` |
| `supported_source_policy_ids` | `{"community-ai-usage-policy:1.0"}` |
| `supported_assessment_schema_versions` | `frozenset()` (no nested "assessment schema" concept) |
| `supported_operation_catalog_versions` | `frozenset()` (AI uses capability/provider/model catalogs) |
| `supported_capability_catalog_versions` | `{"1.0"}` (`AI_CAPABILITY_CATALOG_VERSION`) |
| `supported_provider_catalog_versions` | `{"1.0"}` (`AI_PROVIDER_FAMILY_CATALOG_VERSION`) |
| `supported_model_catalog_versions` | `{"1.0"}` (`AI_MODEL_FAMILY_CATALOG_VERSION`) |
| `required_path_dimensions` | `("stream", "schema_version", "year", "month", "day")` |
| `optional_path_dimensions` | `()` |
| `s3_metadata_allowlist` | `frozenset(ALLOWED_S3_METADATA_KEYS)` — includes `codestrata-client-type` |
| `forbidden_partition_fields` | `event_id`, `installation_id`, `client_type`, `capability`, `provider_family`, `model_family`, `prompt`, `response`, `cost`, `api_key`, token fields, repository/path/source fields, plus cross-stream identity/shape fields |

Limitations recorded on the policy include
`client_type_in_metadata_not_path`,
`capability_provider_model_remain_private_payload`, and
`no_openrouter_support`.

## Projection flow: `project_ai_usage_storage_object`

```python
from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    project_ai_usage_storage_object,
)

result = project_ai_usage_storage_object(envelope)
# result.storage_object: ImmutableRawStorageObject, with
#   to_s3_metadata() including codestrata-client-type
# result.diagnostics: PartitionProjectionDiagnostics
#   (client_type set; capability/provider/model catalog versions set;
#    operation_catalog_version left None)
```

Order of checks, each raising `PartitionProjectionError` with a bounded,
allowlisted `code`:

1. `stream_mismatch` — `envelope.event_stream` must be `"ai_usage"`.
2. `unsupported_envelope_schema` / `unsupported_source_schema` /
   `unsupported_source_policy` — envelope/source identity must match the
   partition policy's supported sets.
3. `invalid_payload` — the payload must round-trip through
   `AiUsageRequest.model_validate()` (fail-closed typed re-check);
   this also rejects unknown capabilities/providers/models,
   prompt/response/source-shaped extras, exact cost, and raw model IDs.
4. `invalid_client_type` — `envelope.client.client_type` must be one of
   `ALLOWED_AI_USAGE_CLIENTS` *and* must match the revalidated payload's
   `client.name`.
5. `unsupported_capability_catalog` /
   `unsupported_provider_catalog` /
   `unsupported_model_catalog` — each AI catalog version must be in the
   matching partition-policy supported set (catalog-version checks, not
   per-event value checks).
6. `storage_object_invalid` — the resolved
   `ImmutableRawStorageObject` (built via
   `build_immutable_raw_storage_object`, then given the optional
   `codestrata-client-type` extra metadata) must itself validate.
7. `partition_invalid` — the resolved object key and S3 metadata must match
   the partition policy's generic dimensions and metadata allowlist.

This function **never calls a store** — persistence is the caller's
responsibility.

### Catalog aliases produce identical storage bytes

Capability / provider / model field validators canonicalize through their
catalogs before the model is ever constructed — so submitting a real
catalog alias (e.g. `"modernization-advisor"` or `"ai_enrichment"`, which
canonicalize to `"modernization_advisor"`; `"bedrock"` → `"aws_bedrock"`;
`"gpt"` → `"gpt_family"`) and submitting the canonical value directly
produce byte-identical projected envelopes (same `event_id`, same
`canonical_json_bytes`, same object key).

## Persisting a projection: `store_projected_ai_usage`

```python
from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    store_projected_ai_usage,
)

write_result = store_projected_ai_usage(store, projection)
```

Requires `store.put_immutable_storage_object(storage_object)` — the only
path that writes the *projected* object (including its
`codestrata-client-type` extra metadata) byte-exact, without rebuilding
from the envelope. `store.put_immutable_event(envelope)` alone would
silently drop the projector's extra metadata. Raises `AttributeError` for
any store lacking `put_immutable_storage_object`.

Both stores already expose it:

- `InMemoryCommunityDataLakeStore.put_immutable_storage_object()`
- `CommunityDataLakeS3Store.put_immutable_storage_object()`

## Privacy

- The object key carries only the five generic dimension names/values —
  never `client_type`, `capability`, `provider_family`, `model_family`,
  `outcome`, `event_id`, or `installation_id`.
- S3 metadata carries the five base keys **plus**
  `codestrata-client-type` — never `capability`, `provider_family`,
  `model_family`, `outcome`, `event_id`, or `installation_id`. The
  client-type *value* (`codestrata_cli` / `vscode_extension` /
  `cursor_extension`) is intentionally present.
- `PartitionProjectionDiagnostics` carries `client_type` and the three
  catalog-version scalars, and structurally excludes `event_id`,
  `installation_id`, the object key, bucket, digest, payload, `capability`,
  `provider_family`, `model_family`, `outcome`, and every prompt/response
  field.
- `PartitionProjectionError.to_stable_dict()` returns only `{"code": ...,
  "detail": ...}` with `detail` bounded to 64 characters.

See `platform/tests/community_cloud_api/data_lake/test_ai_usage_partition_privacy.py`.

## Production unwired

No production wiring file references this module. AI usage collection is
**not** operational via the data lake after this slice — the HTTP endpoint
still uses in-memory / fail-closed sinks. Creating the projector does not
enable acceptance into S3.

## Relation to Slice 8.9 and future anonymous analytics

Slice 8.9 (and later) is expected to address endpoint → storage wiring,
durable event identity, and/or analytics consumers. This slice does not
start that work. Future anonymous analytics / Glue / Athena consumers may
use the Hive path and (for this stream) the bounded
`codestrata-client-type` metadata filter, but no such consumer exists in
this repository yet.

## Testing

```bash
.venv/bin/pytest platform/tests/community_cloud_api/data_lake -k 'ai_usage_partition or ai_usage_storage' -q
.venv/bin/pytest platform/tests/community_cloud_api/data_lake -q
```

New Slice 8.8 test modules:

- `test_ai_usage_partition_policy.py` — policy shape, including the three
  AI catalog version frozensets, empty operation catalog, and client-type
  in the S3 metadata allowlist.
- `test_ai_usage_partitioning.py` — projector happy paths (CLI / VS Code /
  Cursor clients, capability/provider/model aliases) and every
  `PartitionProjectionError` code, including the three unsupported-catalog
  codes.
- `test_ai_usage_partition_privacy.py` — object key, S3 metadata, and
  diagnostics never carry forbidden field values or keys; metadata may
  carry `codestrata-client-type`; diagnostics may carry catalog versions
  (not capability/provider values).
- `test_ai_usage_storage_projection.py` — end-to-end request →
  envelope → projection → in-memory store and fake-S3 store integration
  (`STORED` / `ALREADY_EXISTS` / `CONFLICT`), including
  `put_immutable_event()` alone dropping client-type metadata.
- `test_ai_usage_partition_determinism.py` — repeated projection is
  byte-identical; alias vs canonical identical; client types differ;
  meaningful provider change changes digest; date dimensions track the
  fixed acceptance clock.
- `test_ai_usage_partition_compatibility.py` — every version stays
  pinned; the five partition policies remain distinct; prior streams leave
  the three AI catalog frozensets empty; CLI still excludes client-type
  from its allowlist while AI usage includes it.
- `test_ai_usage_partition_boundary.py` — no production wiring /
  endpoint / Engine references any Slice 8.8 symbol; extra path dimensions
  (`capability=`, `provider_family=`, `model_family=`, `client_type=`) and
  path traversal rejected; S3 store still has
  `put_immutable_storage_object` and no delete/list.

## Limitations (Slice 8.8)

- No endpoint → storage wiring (still Slice 8.1–8.7's posture)
- Does not start Slice 8.9
- No extra partition path dimension for this stream — `client_type`,
  `capability`, `provider_family`, and `model_family` all remain outside
  the path; only `client_type` is surfaced in S3 metadata (Option B)
- Capability / provider / model / outcome / buckets remain
  private-payload-only
- Prompt / response / exact cost / raw model IDs remain rejected
- `installation_id` remains private-payload-only
- No OpenRouter support
- This module only projects — it never wires a store, an endpoint, or an
  emitter
- AI usage collection is not claimed operational via the data lake
- No durable event-identity/deduplication store
- No OpenTofu / IAM change

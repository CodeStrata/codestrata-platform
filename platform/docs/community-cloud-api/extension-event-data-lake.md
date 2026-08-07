# Extension Event Partitioning (Slice 8.7)

Slice 8.7 gives the `extension_event` event stream its own versioned
**partition policy** and a stream-specific **storage-object projector**,
built on top of the Slice 8.1–8.6 Community Data Lake foundation and
reusing the exact same generic (stream-agnostic) partitioning machinery
[Slice 8.4](./assessment-metadata-data-lake.md) introduced for
`assessment_metadata`, [Slice 8.5](./telemetry-data-lake.md) reused for
`telemetry`, and [Slice 8.6](./cli-event-data-lake.md) reused for
`cli_event`.

See [data-lake.md](./data-lake.md) (Slice 8.1 foundation),
[immutable-raw-storage.md](./immutable-raw-storage.md) (Slice 8.2 storage
contract), [data-lake-event-envelope.md](./data-lake-event-envelope.md)
(Slice 8.3 envelope/registry), and the Slice 8.4–8.6 stream docs for what
this slice builds on.

## What this slice does NOT do

- **Does not wire any endpoint to S3.** `app.py`, `deployment/wiring.py`,
  `deployment/settings.py`, the extension event endpoint's own
  `routes.py`/`service.py`/`ports.py`, the VS Code extension
  emitters, and the telemetry runtime are all unchanged — see
  `platform/tests/community_cloud_api/data_lake/test_extension_event_partition_boundary.py`.
- **Does not start Slice 8.8.** Partition policy ownership for `ai_usage`
  followed in [Slice 8.8](./ai-usage-data-lake.md); this slice stops at
  `extension_event`.
- **Does not bump any schema version.** Envelope schema and the extension
  event endpoint schema both stay `1.0`. The extension operation catalog
  also stays `1.0`. Only the **new** partition policy is versioned, at
  `1.0`.
- **Does not change emitters.** No VS Code, CLI, or Engine change
  accompanies this slice.
- **Does not claim extension collection is operational.** The endpoint and
  sinks remain fail-closed / in-memory in production; this slice only adds
  an unwired projector.
- **Does not commit, plan, or apply any OpenTofu change.**
- **Does not add a durable event-identity/deduplication store.**

## Partition dimension decision

**Decision: retain the generic Hive path only** — identical in shape to the
`assessment_metadata`, `telemetry`, and `cli_event` streams:

```text
raw/stream=extension_event/schema_version=1.0/year=YYYY/month=MM/day=DD/{opaque}.json
```

No dimension is added for `client_type`, `editor`, `operation`,
`lifecycle`, `result`, `failure_category`, `invocation_source`, workspace /
report state, or assessment heads. Rationale:

- **Cross-stream path consistency.** Every registered stream keeps the
  accepted path at exactly `stream=` / `schema_version=` / `year=` /
  `month=` / `day=` — a fourth stream reusing the identical shape keeps any
  future shared Glue/Athena catalog definition simple.
- **`operation` is an analytics dimension whose catalog evolves.** The
  extension operation catalog
  (`codestrata_platform.community_cloud_api.extension_events.catalog`) is
  explicitly versioned (`EXTENSION_OPERATION_CATALOG_VERSION`, currently
  `1.0`) because command IDs grow and rename over time. Baking `operation`
  into the physical storage path would force a partition-layout migration
  on every catalog change — the same reasoning Slice 8.5 applied to
  telemetry's `event_type` and Slice 8.6 applied to CLI operations.
- **`client_type` / `editor` as path dimensions are unnecessary.** The pair
  is one-to-one today (`vscode_extension`↔`vscode`,
  `cursor_extension`↔`cursor`). Cardinality is only two values, but the
  value is already carried in S3 metadata (Option B below) and in the
  private payload, so a fourth copy in the path buys nothing and would
  fragment prefixes without a reader in this repository today.
- **`lifecycle` / `result` / `failure_category` / context fields are
  private-payload analytics fields**, not stable transport-classification
  concepts.

## S3 metadata decision (Option B)

**Decision: one bounded stream-specific S3 metadata key —
`codestrata-client-type`.** This reuses the existing
`ALLOWED_S3_METADATA_KEYS` entry introduced for telemetry in Slice 8.5 —
**no** synonym such as `codestrata-extension-client` or
`codestrata-editor` is introduced.

| Candidate | Disposition | Rationale |
| --- | --- | --- |
| `client.name` (→ `client_type`) | **S3 metadata** (`codestrata-client-type`) | Two first-party clients (`vscode_extension` active; `cursor_extension` historical-only) — a coarse operational filter that mirrors telemetry |
| `client.editor` | Private payload only | One-to-one with client type today; attaching both would be redundant |
| `event.operation` | Private payload only | Analytics vocabulary tied to the versioned, evolving operation catalog |
| `event.lifecycle` / `event.result` / `event.failure_category` | Private payload only | Analytics/outcome fields belonging to future aggregate processing |
| `context.*` (workspace/report/invocation) | Private payload only | Anonymous execution-context classification; no consumer needs it in metadata/path yet |
| `event_id` | Private payload only | Approved endpoint field; never in key/metadata/diagnostics |
| `installation_id` | Private payload only | Approved endpoint field; optional, still never in key/metadata/diagnostics |

Rationale for Option B over Option A (generic metadata only, as CLI chose
in Slice 8.6): unlike `cli_event` (always `codestrata_cli`), this stream
legitimately separates VS Code versus historical Cursor client-type objects
(active projection is VS Code only — Slice 12.4).

`project_extension_event_storage_object` therefore calls
`merge_extra_s3_metadata` exactly once for `codestrata-client-type`, and
persistence **must** go through `store_projected_extension_event` /
`put_immutable_storage_object` so that extra metadata is not dropped by an
envelope rebuild.

## The extension event partition policy

```python
from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    default_extension_event_partition_policy,
)

policy = default_extension_event_partition_policy()
policy.policy_token  # "community-extension-event-partition-policy:1.0"
```

| Field | Value |
| --- | --- |
| `policy_id` | `community-extension-event-partition-policy` |
| `policy_version` | `1.0` |
| `event_stream` | `extension_event` |
| `supported_envelope_schema_versions` | `{"1.0"}` |
| `supported_source_schema_versions` | `{"1.0"}` |
| `supported_source_policy_ids` | `{"community-extension-event-policy:1.0"}` |
| `supported_assessment_schema_versions` | `frozenset()` (no nested "assessment schema" concept) |
| `supported_operation_catalog_versions` | `{"1.0"}` (`EXTENSION_OPERATION_CATALOG_VERSION`) |
| `required_path_dimensions` | `("stream", "schema_version", "year", "month", "day")` |
| `optional_path_dimensions` | `()` |
| `s3_metadata_allowlist` | `frozenset(ALLOWED_S3_METADATA_KEYS)` — includes `codestrata-client-type` |
| `forbidden_partition_fields` | `event_id`, `installation_id`, `client_type`, `editor`, `operation`, `lifecycle`, `result`, workspace/document/repository/path/command fields, plus cross-stream identity/shape fields |

Limitations recorded on the policy include
`client_type_in_metadata_not_path`, `operation_remains_private_payload`, and
`editor_remains_private_payload`.

## Projection flow: `project_extension_event_storage_object`

```python
from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    project_extension_event_storage_object,
)

result = project_extension_event_storage_object(envelope)
# result.storage_object: ImmutableRawStorageObject, with
#   to_s3_metadata() including codestrata-client-type
# result.diagnostics: PartitionProjectionDiagnostics
#   (client_type set, operation_catalog_version set)
```

Order of checks, each raising `PartitionProjectionError` with a bounded,
allowlisted `code`:

1. `stream_mismatch` — `envelope.event_stream` must be `"extension_event"`.
2. `unsupported_envelope_schema` / `unsupported_source_schema` /
   `unsupported_source_policy` — envelope/source identity must match the
   partition policy's supported sets.
3. `invalid_payload` — the payload must round-trip through
   `ExtensionEventRequest.model_validate()` (fail-closed typed re-check);
   this also rejects unknown operations, client/editor pair mismatches, and
   workspace/document/path-shaped extras.
4. `invalid_client_type` — `envelope.client.client_type` must be one of
   `ALLOWED_EXTENSION_CLIENTS` *and* must match the revalidated payload's
   `client.name`.
5. `unsupported_operation_catalog` —
   `EXTENSION_OPERATION_CATALOG_VERSION` must be one of the partition
   policy's `supported_operation_catalog_versions` (catalog-version check,
   not a per-event `operation` value check).
6. `storage_object_invalid` — the resolved
   `ImmutableRawStorageObject` (built via
   `build_immutable_raw_storage_object`, then given the optional
   `codestrata-client-type` extra metadata) must itself validate.
7. `partition_invalid` — the resolved object key and S3 metadata must match
   the partition policy's generic dimensions and metadata allowlist.

This function **never calls a store** — persistence is the caller's
responsibility.

### Operation aliases produce identical storage bytes

`ExtensionEvent.operation`'s field validator canonicalizes through the
extension operation catalog before the model is ever constructed — so
submitting a real catalog alias (e.g. `"codestrata.openHtmlReport"`, which
canonicalizes to `"open_report"`) and submitting the canonical value
directly produce byte-identical projected envelopes (same `event_id`, same
`canonical_json_bytes`, same object key).

## Persisting a projection: `store_projected_extension_event`

```python
from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    store_projected_extension_event,
)

write_result = store_projected_extension_event(store, projection)
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
  never `client_type`, `editor`, `operation`, `lifecycle`, `result`,
  `event_id`, or `installation_id`.
- S3 metadata carries the five base keys **plus**
  `codestrata-client-type` — never `editor`, `operation`, `lifecycle`,
  `event_id`, or `installation_id`. The client-type *value*
  (`vscode_extension` active; `cursor_extension` historical-only) is intentionally present.
- `PartitionProjectionDiagnostics` carries both `client_type` and
  `operation_catalog_version`, and structurally excludes `event_id`,
  `installation_id`, the object key, bucket, digest, payload, `operation`,
  `editor`, `lifecycle`, `result`, and every context field.
- `PartitionProjectionError.to_stable_dict()` returns only `{"code": ...,
  "detail": ...}` with `detail` bounded to 64 characters.

See `platform/tests/community_cloud_api/data_lake/test_extension_event_partition_privacy.py`.

## Production unwired

No production wiring file references this module. Extension collection is
**not** operational via the data lake after this slice — the HTTP endpoint
still uses in-memory / fail-closed sinks. Creating the projector does not
enable acceptance into S3.

## Relation to Slice 8.8 and future anonymous analytics

[Slice 8.8](./ai-usage-data-lake.md) gives `ai_usage` its own partition
policy and projector on the same generic machinery. This slice does not
start that work (or Slice 8.9). Future anonymous analytics / Glue / Athena
consumers may use the Hive path and (for this stream) the bounded
`codestrata-client-type` metadata filter, but no such consumer exists in
this repository yet.

## Testing

```bash
.venv/bin/pytest platform/tests/community_cloud_api/data_lake -k extension_event_partition -q
.venv/bin/pytest platform/tests/community_cloud_api/data_lake -q
```

New Slice 8.7 test modules:

- `test_extension_event_partition_policy.py` — policy shape, including
  `supported_operation_catalog_versions` and client-type in the S3
  metadata allowlist.
- `test_extension_event_partitioning.py` — projector happy paths (VS Code /
  Cursor clients, operation alias) and every
  `PartitionProjectionError` code, including
  `unsupported_operation_catalog`.
- `test_extension_event_partition_privacy.py` — object key, S3 metadata,
  and diagnostics never carry forbidden field values or keys; metadata may
  carry `codestrata-client-type`.
- `test_extension_event_storage_projection.py` — end-to-end request →
  envelope → projection → in-memory store and fake-S3 store integration
  (`STORED` / `ALREADY_EXISTS` / `CONFLICT`), including
  `put_immutable_event()` alone dropping client-type metadata.
- `test_extension_event_partition_determinism.py` — repeated projection is
  byte-identical; alias vs canonical identical; active VS Code projection
  succeeds; retired Cursor active projection rejected (Slice 12.4);
  date dimensions track the fixed acceptance clock.
- `test_extension_event_partition_compatibility.py` — every version stays
  pinned; the four partition policies remain distinct; CLI still excludes
  client-type from its allowlist while extension includes it.
- `test_extension_event_partition_boundary.py` — no production wiring /
  endpoint / Engine / VS Code plugin references any Slice 8.7
  symbol; extra path dimensions and path traversal rejected; S3 store still
  has `put_immutable_storage_object` and no delete/list.

## Limitations (Slice 8.7)

- No endpoint → storage wiring (still Slice 8.1–8.6's posture)
- Partition policy for `ai_usage` followed in
  [Slice 8.8](./ai-usage-data-lake.md); this slice does not start Slice 8.9
- No extra partition path dimension for this stream — `client_type`,
  `editor`, and `operation` all remain outside the path; only
  `client_type` is surfaced in S3 metadata (Option B)
- `operation` / `editor` / `lifecycle` / `result` remain
  private-payload-only
- `installation_id` remains private-payload-only
- This module only projects — it never wires a store, an endpoint, or an
  emitter
- Extension collection is not claimed operational via the data lake
- No durable event-identity/deduplication store
- No OpenTofu / IAM change

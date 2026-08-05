# CLI Event Partitioning (Slice 8.6)

Slice 8.6 gives the `cli_event` event stream its own versioned **partition
policy** and a stream-specific **storage-object projector**, built on top of
the Slice 8.1–8.5 Community Data Lake foundation and reusing the exact same
generic (stream-agnostic) partitioning machinery
[Slice 8.4](./assessment-metadata-data-lake.md) introduced for
`assessment_metadata` and [Slice 8.5](./telemetry-data-lake.md) reused
unchanged for `telemetry`.

See [data-lake.md](./data-lake.md) (Slice 8.1 foundation),
[immutable-raw-storage.md](./immutable-raw-storage.md) (Slice 8.2 storage
contract), [data-lake-event-envelope.md](./data-lake-event-envelope.md)
(Slice 8.3 envelope/registry), and
[assessment-metadata-data-lake.md](./assessment-metadata-data-lake.md) /
[telemetry-data-lake.md](./telemetry-data-lake.md) (Slices 8.4/8.5 — the
generic machinery this slice reuses unchanged) for what this slice builds
on.

## What this slice does NOT do

- **Does not wire any endpoint to S3.** `app.py`, `deployment/wiring.py`,
  `deployment/settings.py`, the CLI event endpoint's own
  `routes.py`/`service.py`/`ports.py`, the CLI emitter, and the telemetry
  runtime are all unchanged — see
  `platform/tests/community_cloud_api/data_lake/test_cli_event_partition_boundary.py`.
- **Does not start Slice 8.7 / 8.8.** This slice stops at `cli_event`.
  Slice 8.7 later adds the `extension_event` partition policy;
  [Slice 8.8](./ai-usage-data-lake.md) later adds the `ai_usage` partition
  policy.
- **Does not bump any schema version.** Envelope schema and the CLI event
  endpoint schema both stay `1.0`. The CLI operation catalog also stays
  `1.0`. Only the **new** partition policy is versioned, at `1.0`.
- **Does not add any new S3 metadata key at all.** Unlike Slice 8.4
  (`codestrata-assessment-schema`) and Slice 8.5
  (`codestrata-client-type`), this stream's `s3_metadata_allowlist` is
  exactly the five generic base keys — no CLI-specific metadata key is
  introduced (see dimension decision below).
- **Does not commit, plan, or apply any OpenTofu change.**
- **Does not add a durable event-identity/deduplication store.**

## Partition dimension decision

**Decision: retain the generic Hive path only** — identical in shape to the
`assessment_metadata` and `telemetry` streams:

```text
raw/stream=cli_event/schema_version=1.0/year=YYYY/month=MM/day=DD/{opaque}.json
```

No dimension is added for `operation`, `lifecycle`, `result`,
`failure_category`, `client_type`, or `invocation_source`. Rationale:

- **Cross-stream path consistency.** Every stream registered so far
  (`assessment_metadata`, `telemetry`, and now `cli_event`) keeps the
  accepted path at exactly `stream=` / `schema_version=` / `year=` /
  `month=` / `day=` — a fourth stream reusing the identical shape keeps any
  future shared Glue/Athena catalog definition simple.
- **`operation` is an analytics dimension whose catalog evolves.** The CLI
  operation catalog
  (`codestrata_platform.community_cloud_api.cli_events.catalog`) is
  explicitly versioned (`CLI_OPERATION_CATALOG_VERSION`, currently `1.0`)
  *because* it is expected to gain, rename, or retire canonical operations
  as the public CLI surface grows. Baking `operation` into the physical
  storage path would force a partition-layout migration every time the
  catalog changes — exactly the same reasoning Slice 8.5 applied to
  telemetry's `event_type`.
- **`client_type` is redundant for this stream — not just as a path
  dimension, but at all.** Unlike `telemetry`/`assessment_metadata`, which
  accept multiple client types, the `cli_event` stream's source contract
  allowlists exactly one client: `codestrata_cli` (see
  `CLI_CLIENT_NAME`). A dimension whose value is always constant carries
  zero information, whether it lives in the path or in S3 metadata — this
  is why Slice 8.6 omits `client_type` entirely rather than merely keeping
  it out of the path the way Slice 8.5 kept `event_type` out of the path
  while still surfacing `client_type` in metadata.
- **`lifecycle` / `result` / `failure_category` / `invocation_source` are
  private-payload analytics fields**, not stable transport-classification
  concepts. None has a filtering consumer in this repository today, and
  `failure_category` in particular is effectively open-ended relative to
  the fixed five-dimension generic path every stream already uses.

## S3 metadata decision

**Decision: no new S3 metadata key at all — the allowlist is exactly the
five base keys.**

| Candidate | Disposition | Rationale |
| --- | --- | --- |
| `client.name` (→ `client_type`) | Private payload only — **not even S3 metadata** | Always `codestrata_cli`; a constant value has no filtering power, unlike telemetry's three-member vocabulary |
| `event.operation` | Private payload only | Analytics vocabulary tied to the versioned, evolving operation catalog — see dimension decision above |
| `event.lifecycle` / `event.result` / `event.failure_category` | Private payload only | Analytics/outcome fields belonging to future aggregate processing, not raw-object partitioning |
| `event.duration_bucket` | Private payload only | Already-bucketed analytics field, mirrors telemetry's `properties.duration_bucket` disposition |
| `context.invocation_source` / `.terminal_environment` / `.execution_mode` / `.output_format` | Private payload only | Anonymous execution-context classification; no consumer needs it in metadata/path yet |
| `context.selected_assessment_heads` | Private payload only | Bounded list, but per-repository-selection cardinality; no consumer needs it in metadata/path |
| `event_id` | Private payload only | Approved endpoint field (Slice 7.9); never in key/metadata/diagnostics |
| `installation_id` | Private payload only | Approved endpoint field (Slice 7.9); optional, still never in key/metadata/diagnostics |

**Approved private-payload fields** (every endpoint `CliEvent`/`CliEventContext`
field, `event_id`, the optional `installation_id`): unchanged from the
Slice 7.9 endpoint contract — Slice 8.6 adds no new restriction on what may
be inside the stored `payload` block.

**Metadata candidates used:** none. The projected storage object's
`to_s3_metadata()` returns exactly the five base keys
(`codestrata-content-sha256`, `codestrata-envelope-schema`,
`codestrata-source-schema`, `codestrata-stream`, `codestrata-object-id`) —
see `BASE_S3_METADATA_KEYS`, now exported publicly from `objects.py` for
this policy to reference directly instead of duplicating the literal set.

**Prohibited for partition path or S3 metadata:** `operation`, `lifecycle`,
`result`, `failure_category`, `duration_bucket`, `invocation_source`,
`command`, `command_line`, `argv`, `cwd`, `repository*`, `path`, `file`,
`source`, `terminal*`, every assessment-head field,
`client_version`/`platform`, plus the cross-stream identity/shape fields
already forbidden for the other two registered streams (`installation_id`,
`event_id`, `language`, `executed_heads`, `assessment_status`,
`assessment_schema_version`). See `forbidden_partition_fields` below for the
full enforced list.

## New generic (stream-agnostic) machinery reused unchanged

```text
platform/src/codestrata_platform/community_cloud_api/data_lake/
  partition_policies.py    # StreamPartitionPolicy — +supported_operation_catalog_versions field
  stream_partitions.py       # object-key-vs-policy validation — unchanged
  partition_diagnostics.py     # PartitionProjectionDiagnostics — +operation_catalog_version field
  stream_storage.py              # StorageProjectionResult + merge_extra_s3_metadata() — unchanged (unused by this stream)
  objects.py                       # BASE_S3_METADATA_KEYS — now public (was _BASE_S3_METADATA_KEYS)
  streams/
    assessment_metadata_partitioning.py   # Slice 8.4 policy + projector (unchanged)
    telemetry_partitioning.py               # Slice 8.5 policy + projector (unchanged)
    cli_event_partitioning.py                 # the one new Slice 8.6 policy + projector
```

Two structural changes to the shared machinery, both purely additive
(optional fields with empty/`None` defaults, so every Slice 8.4/8.5 test
continues to pass unchanged):

1. `StreamPartitionPolicy` gains
   `supported_operation_catalog_versions: frozenset[str] = frozenset()`
   (mirroring `supported_assessment_schema_versions`'s shape) — normalized
   to a frozenset in `__post_init__` and included in `to_stable_dict()`.
   `assessment_metadata` and `telemetry` both leave it at the empty
   default; only the `cli_event` policy sets it to
   `frozenset({CLI_OPERATION_CATALOG_VERSION})`.
2. `PartitionProjectionDiagnostics` gains
   `operation_catalog_version: str | None = None` (mirroring
   `assessment_schema_version`/`client_type`'s shape) — validated as a
   bounded non-blank string when present, included in `to_stable_dict()`
   only when set. Only the `cli_event` projector sets it; the other two
   projectors continue to leave it `None`.
3. `objects.py`'s `_BASE_S3_METADATA_KEYS` is renamed to the public
   `BASE_S3_METADATA_KEYS` (a `_BASE_S3_METADATA_KEYS` alias remains for any
   pre-existing internal reference) so the `cli_event` partition policy can
   set `s3_metadata_allowlist=frozenset(BASE_S3_METADATA_KEYS)` directly
   instead of duplicating the five-key literal.

See [data-lake.md](./data-lake.md),
[assessment-metadata-data-lake.md](./assessment-metadata-data-lake.md), and
[telemetry-data-lake.md](./telemetry-data-lake.md) for everything else
about this machinery, which is unchanged.

## The CLI event partition policy

```python
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    default_cli_event_partition_policy,
)

policy = default_cli_event_partition_policy()
policy.policy_token  # "community-cli-event-partition-policy:1.0"
```

| Field | Value |
| --- | --- |
| `policy_id` | `community-cli-event-partition-policy` |
| `policy_version` | `1.0` |
| `event_stream` | `cli_event` |
| `supported_envelope_schema_versions` | `{"1.0"}` |
| `supported_source_schema_versions` | `{"1.0"}` |
| `supported_source_policy_ids` | `{"community-cli-event-policy:1.0"}` |
| `supported_assessment_schema_versions` | `frozenset()` (cli_event has no nested "assessment schema" concept) |
| `supported_operation_catalog_versions` | `{"1.0"}` (`CLI_OPERATION_CATALOG_VERSION`) — the first stream to use this new field |
| `required_path_dimensions` | `("stream", "schema_version", "year", "month", "day")` |
| `optional_path_dimensions` | `()` |
| `s3_metadata_allowlist` | exactly the 5 base keys — `frozenset(BASE_S3_METADATA_KEYS)`, **not** the package-wide `ALLOWED_S3_METADATA_KEYS` (which includes the other streams' optional keys) |
| `forbidden_partition_fields` | `event_id`, `installation_id`, `request_id`, `ip`, `ip_address`, `client_type`, `client_version`, `platform`, `operation`, `lifecycle`, `result`, `failure_category`, `duration_bucket`, `invocation_source`, `execution_mode`, `output_format`, `offline_mode`, `ai_requested`, `selected_assessment_heads`, `terminal_environment`, `command`, `command_line`, `argv`, `args`, `arguments`, `cwd`, `working_directory`, `repository`, `repository_name`, `repository_path`, `repository_url`, `path`, `file`, `file_path`, `filename`, `source`, `source_code`, `terminal`, `terminal_history`, `shell_history`, `stdout`, `stderr`, `exception`, `exception_message`, `stack_trace`, `language`, `executed_heads`, `assessment_status`, `assessment_schema_version` |

## `project_cli_event_storage_object`

```python
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    project_cli_event_storage_object,
)

result = project_cli_event_storage_object(envelope)
# result.storage_object: ImmutableRawStorageObject, with
#   to_s3_metadata() == exactly the 5 base keys (no extra metadata attached)
# result.diagnostics: PartitionProjectionDiagnostics (operation_catalog_version set,
#   client_type=None, assessment_schema_version=None)
```

Order of checks, each raising `PartitionProjectionError` with a bounded,
allowlisted `code` (never raw exception text or payload fragments):

1. `stream_mismatch` — `envelope.event_stream` must be `"cli_event"`.
2. `unsupported_envelope_schema` / `unsupported_source_schema` /
   `unsupported_source_policy` — envelope/source identity must match the
   partition policy's supported sets.
3. `invalid_payload` — the payload must round-trip through
   `CliEventRequest.model_validate()` (fail-closed typed re-check) — this
   also rejects a corrupted/unsupported `operation` (the model's field
   validator enforces the CLI operation catalog allowlist via
   `CliOperationCatalog.canonicalize()`) and any command/argv/cwd-shaped
   extra field, since `CliEventContext`/`CliEvent` use `extra="forbid"`.
4. `invalid_client_type` — `envelope.client.client_type` must equal
   `CLI_CLIENT_NAME` (`"codestrata_cli"`) *and* must match the revalidated
   payload's `client.name` — both sides are checked independently so
   neither can be silently trusted alone.
5. `unsupported_operation_catalog` — `CLI_OPERATION_CATALOG_VERSION` must be
   one of the partition policy's `supported_operation_catalog_versions`.
   This is a *catalog-version* check, not a per-event `operation` value
   check — it confirms the projector is validating against the operation
   catalog version the partition policy expects, independent of which
   specific canonical operation (or alias) the submitted event used.
6. `storage_object_invalid` — `build_immutable_raw_storage_object()` must
   succeed, and the resulting object must itself validate. **No extra
   metadata is ever merged in** — unlike the `assessment_metadata` and
   `telemetry` projectors, this function never calls
   `merge_extra_s3_metadata()`, since the base object *is* the final
   storage object for this stream (see S3 metadata decision above).
7. `partition_invalid` — the resolved object key and S3 metadata must match
   the partition policy's generic dimensions and metadata allowlist
   (exactly the five base keys for this stream).

This function **never calls a store** — it only resolves and validates a
`StorageProjectionResult`. Persistence is the caller's responsibility. There
is no `unsupported_assessment_schema` / `missing_assessment_schema` code
here — `cli_event` carries no nested "assessment schema" concept, exactly
like `telemetry`.

### Operation aliases produce identical storage bytes

`CliEvent.operation`'s field validator canonicalizes through
`CliOperationCatalog.canonicalize()` before the model is ever constructed —
so submitting a real catalog alias (e.g. `"report.open"`, which
canonicalizes to `"open"`) and submitting the canonical value directly
produce byte-identical projected envelopes (same `event_id`, same
`canonical_json_bytes`, same object key), since the payload stored is
always the canonicalized form. See
`test_cli_event_partition_determinism.py::test_operation_alias_and_canonical_operation_produce_the_same_envelope_bytes`.

## Persisting a projection: `store_projected_cli_event`

```python
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    store_projected_cli_event,
)

write_result = store_projected_cli_event(store, projection)
```

Requires `store.put_immutable_storage_object(storage_object)` — mirrors
`store_projected_telemetry` / `store_projected_assessment_metadata` exactly,
for cross-stream consistency, even though this stream's projection carries
no extra metadata to lose if a caller instead used
`store.put_immutable_event(envelope)` directly (unlike the other two
streams, where that path would silently drop the projector's extra
metadata). Raises `AttributeError` for any store lacking
`put_immutable_storage_object`.

Both stores already expose it (added in Slice 8.2 / Slice 8.4, unchanged by
this slice):

- `InMemoryCommunityDataLakeStore.put_immutable_storage_object()`
- `CommunityDataLakeS3Store.put_immutable_storage_object()`

## Privacy

- The object key carries only the five generic dimension names/values —
  never `operation`, `lifecycle`, `result`, `client_type`, `event_id`, or
  `installation_id`.
- S3 metadata carries only the five generic base keys — never `operation`,
  `lifecycle`, `result`, `failure_category`, `duration_bucket`,
  `invocation_source`, `event_id`, or `installation_id`. This stream
  attaches **no** stream-specific metadata key at all.
- `PartitionProjectionDiagnostics` carries `operation_catalog_version` but
  structurally excludes `event_id`, `installation_id`, the object key,
  bucket, digest, payload, `operation`, `lifecycle`, `result`, and every
  context field — see its fixed field list in
  [data-lake.md](./data-lake.md). `client_type` is left `None` for this
  stream's diagnostics (redundant, since it is always `codestrata_cli`).
- `PartitionProjectionError.to_stable_dict()` returns only `{"code": ...,
  "detail": ...}` with `detail` bounded to 64 characters — never the
  original exception text or payload.

See `platform/tests/community_cloud_api/data_lake/test_cli_event_partition_privacy.py`.

## Testing

```bash
.venv/bin/pytest platform/tests/community_cloud_api/data_lake -q
.venv/bin/pytest platform/tests/community_cloud_api -q
```

New Slice 8.6 test modules:

- `test_cli_event_partition_policy.py` — `default_cli_event_partition_policy()`'s
  exact shape, including the new `supported_operation_catalog_versions`
  field and the exactly-five-base-key `s3_metadata_allowlist`.
- `test_cli_event_partitioning.py` — `project_cli_event_storage_object()`
  happy paths (including an operation-alias submission) and every
  `PartitionProjectionError` code, including the new
  `unsupported_operation_catalog` code.
- `test_cli_event_partition_privacy.py` — object key, S3 metadata, and
  diagnostics never carry forbidden field values or keys; S3 metadata is
  exactly the five base keys with no extra.
- `test_cli_event_storage_projection.py` — end-to-end request → envelope →
  projection → in-memory store and fake-S3 store integration (`STORED` /
  `ALREADY_EXISTS` / `CONFLICT`).
- `test_cli_event_partition_determinism.py` — repeated projection is
  byte-identical; different event keys/dates produce different
  keys/prefixes deterministically; a real catalog alias (`"report.open"`)
  and its canonical operation (`"open"`) produce byte-identical envelopes.
- `test_cli_event_partition_compatibility.py` — every version stays pinned;
  the three partition policies (`cli_event`, `telemetry`,
  `assessment_metadata`) remain distinct.
- `test_cli_event_partition_boundary.py` — no production wiring file (the
  CLI event endpoint's own `routes.py`/`service.py`/`ports.py`, the
  telemetry runtime, or the Engine/CLI package) references any Slice 8.6
  symbol or `data_lake` at all; CLI-event-specific partition-key rejection
  paths (`operation=`/`client_type=` as an extra dimension, stream/date
  mismatches).

`test_telemetry_partition_privacy.py`, `test_assessment_metadata_partition_privacy.py`,
and every other Slice 8.4/8.5 test continue to pass unchanged —
`operation_catalog_version` on `PartitionProjectionDiagnostics` and
`supported_operation_catalog_versions` on `StreamPartitionPolicy` are both
optional and default to `None`/empty.

## Limitations (Slice 8.6)

- No endpoint → storage wiring (still Slice 8.1–8.5's posture)
- No partition policy yet for `ai_usage` at the time of this slice;
  `extension_event` and `ai_usage` received theirs in Slices 8.7 /
  [8.8](./ai-usage-data-lake.md)
- No extra partition path dimension for this stream — `operation`,
  `lifecycle`, `result`, `failure_category`, `client_type`, and
  `invocation_source` all remain outside the path (see dimension decision
  above); none of them is ever surfaced in S3 metadata either
- `operation` remains private-payload-only — the operation catalog is
  expected to evolve, so it never becomes a storage-layout concern
- `lifecycle`/`result` remain private-payload-only
- `installation_id` remains private-payload-only, exactly like the other
  two registered streams
- This module only projects — it never wires a store, an endpoint, the CLI
  emitter, or the telemetry runtime
- No durable event-identity/deduplication store
- No OpenTofu / IAM change

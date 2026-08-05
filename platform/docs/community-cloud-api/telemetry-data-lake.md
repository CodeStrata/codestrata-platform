# Telemetry Partitioning (Slice 8.5)

Slice 8.5 gives the `telemetry` event stream its own versioned **partition
policy** and a stream-specific **storage-object projector**, built on top of
the Slice 8.1–8.4 Community Data Lake foundation and reusing the exact same
generic (stream-agnostic) partitioning machinery
[Slice 8.4](./assessment-metadata-data-lake.md) introduced for
`assessment_metadata`.

See [data-lake.md](./data-lake.md) (Slice 8.1 foundation),
[immutable-raw-storage.md](./immutable-raw-storage.md) (Slice 8.2 storage
contract), [data-lake-event-envelope.md](./data-lake-event-envelope.md)
(Slice 8.3 envelope/registry), and
[assessment-metadata-data-lake.md](./assessment-metadata-data-lake.md)
(Slice 8.4 — the first concrete `StreamPartitionPolicy` and the generic
machinery this slice reuses unchanged) for what this slice builds on.

## What this slice does NOT do

- **Does not wire any endpoint to S3.** `app.py`, `deployment/wiring.py`,
  `deployment/settings.py`, and every endpoint service are unchanged — see
  `platform/tests/community_cloud_api/data_lake/test_telemetry_partition_boundary.py`.
- **Does not start Slice 8.6+.** This slice stops at `telemetry`. Later
  slices add partition policies for `cli_event` (8.6), `extension_event`
  (8.7), and `ai_usage` ([8.8](./ai-usage-data-lake.md)).
- **Does not bump any schema version.** Envelope schema and the telemetry
  endpoint schema both stay `1.0`. Only the **new** partition policy is
  versioned, at `1.0`.
- **Does not add any new S3 metadata key beyond `codestrata-client-type`.**
  In particular, it does **not** add a `codestrata-telemetry-event-type`
  key — `event_type` stays private-payload-only (see dimension decision
  below).
- **Does not commit, plan, or apply any OpenTofu change.**
- **Does not add a durable event-identity/deduplication store.**

## Partition dimension decision

**Decision: retain the generic Hive path only** — identical in shape to the
`assessment_metadata` stream:

```text
raw/stream=telemetry/schema_version=1.0/year=YYYY/month=MM/day=DD/{opaque}.json
```

No dimension is added for `client_type` or `event_type`. Rationale:

- **Cross-stream path consistency.** Keeping every stream's accepted path at
  exactly `stream=` / `schema_version=` / `year=` / `month=` / `day=`
  simplifies any future shared Glue/Athena catalog definition across all
  five streams — the same reasoning Slice 8.4 applied to
  `assessment_metadata`.
- **Avoid lifecycle/prefix fragmentation.** Splitting the `raw/stream=
  telemetry/...` prefix by client type or event type would multiply the
  number of S3 prefixes (and any future lifecycle/retention rule scoped to
  them) without a corresponding reader in this repository today.
- **`client_type` vocabulary is small but the path dimension is
  unnecessary.** `TelemetryClientName` has exactly three bounded members
  (`codestrata_cli`, `vscode_extension`, `other_extension`) — low
  cardinality — but the value is already carried in S3 metadata (see below)
  and in the private payload's `client.name` field, so a fourth copy in the
  path buys nothing.
- **`event_type` couples storage layout to analytics semantics.** Unlike
  `client_type` (a stable transport-classification concept),
  `TelemetryEventType` is a product/analytics vocabulary expected to evolve
  as new telemetry events are added. Baking it into the physical storage
  path would force a partition-layout migration every time the event-type
  vocabulary changes. `event_type` therefore stays private-payload-only —
  never in the path, never in S3 metadata.

## Property-cardinality review

Before choosing `client_type` as the only metadata candidate, every
`TelemetryIngestionRequest` field was reviewed against the same
"path / metadata / private-payload-only" three-way split Slice 8.4 used for
`assessment_metadata`:

| Field | Disposition | Rationale |
| --- | --- | --- |
| `client.name` (→ `client_type`) | **S3 metadata** (`codestrata-client-type`) | Bounded 3-member vocabulary; useful for coarse per-client filtering without a path dimension |
| `event_id` | Private payload only | Approved endpoint field (Slice 7.7); never in key/metadata/diagnostics |
| `installation_id` | Private payload only | Approved endpoint field (Slice 7.7); optional, still never in key/metadata/diagnostics |
| `occurred_at` | Private payload only | Client-submitted content; never drives the partition date — only the server-assigned `acceptance.accepted_at` does |
| `event_type` | Private payload only | Analytics vocabulary, expected to evolve — see dimension decision above |
| `properties.feature` / `.operation` | Private payload only | Free-labelled (bounded, but effectively per-feature cardinality); no consumer needs them in metadata/path yet |
| `properties.duration_bucket` / `.outcome` | Private payload only | Already-bucketed analytics fields; belong to future aggregate processing, not raw-object partitioning |
| `properties.count` / `.flags` | Private payload only | Numeric/list fields; never partition or metadata material |
| `client.version` / `client.platform` | Private payload only | Free-form-ish version/platform strings; higher cardinality than `client_type` and not needed for partitioning |

**Approved private-payload fields** (all endpoint `TelemetryProperties`
fields, `event_id`, `installation_id`, `occurred_at`): unchanged from the
Slice 7.7 endpoint contract — Slice 8.5 adds no new restriction on what may
be inside the stored `payload` block.

**Metadata candidate used:** `client_type` only.

**Prohibited for partition path or S3 metadata:** `feature`, `operation`,
`duration_bucket`, `outcome`, `count`, `flags`, `installation_id`,
`event_id`, `occurred_at`, `event_type` (path — metadata is also never
added for it), `client_version`, `platform`, plus the cross-stream
identity/shape fields already forbidden for `assessment_metadata`
(`language`, `executed_heads`, `repository_name`, `repository_url`,
`assessment_status`, `assessment_schema_version`) as defense-in-depth. See
`forbidden_partition_fields` below for the full enforced list.

## New generic (stream-agnostic) machinery reused unchanged

```text
platform/src/codestrata_platform/community_cloud_api/data_lake/
  partition_policies.py    # StreamPartitionPolicy — unchanged since Slice 8.4
  stream_partitions.py       # object-key-vs-policy validation — unchanged
  partition_diagnostics.py     # PartitionProjectionDiagnostics — +client_type field
  stream_storage.py              # StorageProjectionResult + merge_extra_s3_metadata() — unchanged
  streams/
    assessment_metadata_partitioning.py   # Slice 8.4 policy + projector (unchanged)
    telemetry_partitioning.py               # the one new Slice 8.5 policy + projector
```

The only structural change to the shared machinery is
`PartitionProjectionDiagnostics` gaining one more optional field,
`client_type: str | None = None` (mirroring the shape of the existing
optional `assessment_schema_version` field) — see
[data-lake.md](./data-lake.md) and
[assessment-metadata-data-lake.md](./assessment-metadata-data-lake.md) for
everything else, which is unchanged. The `assessment_metadata` projector
continues to leave `client_type` `None`; only the `telemetry` projector sets
it.

## The telemetry partition policy

```python
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    default_telemetry_partition_policy,
)

policy = default_telemetry_partition_policy()
policy.policy_token  # "community-telemetry-partition-policy:1.0"
```

| Field | Value |
| --- | --- |
| `policy_id` | `community-telemetry-partition-policy` |
| `policy_version` | `1.0` |
| `event_stream` | `telemetry` |
| `supported_envelope_schema_versions` | `{"1.0"}` |
| `supported_source_schema_versions` | `{"1.0"}` |
| `supported_source_policy_ids` | `{"community-telemetry-policy:1.0"}` |
| `supported_assessment_schema_versions` | `frozenset()` (telemetry has no nested "assessment schema" concept) |
| `required_path_dimensions` | `("stream", "schema_version", "year", "month", "day")` |
| `optional_path_dimensions` | `()` |
| `s3_metadata_allowlist` | the 5 generic keys + `codestrata-assessment-schema` + `codestrata-client-type` (the full package-wide allowlist; only `codestrata-client-type` is ever attached by this stream's projector) |
| `forbidden_partition_fields` | `event_id`, `installation_id`, `request_id`, `ip`, `ip_address`, `client_type`, `client_version`, `platform`, `event_type`, `occurred_at`, `feature`, `operation`, `outcome`, `duration_bucket`, `count`, `flags`, `properties`, `language`, `executed_heads`, `repository_name`, `repository_url`, `assessment_status`, `assessment_schema_version` |

## `project_telemetry_storage_object`

```python
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    project_telemetry_storage_object,
)

result = project_telemetry_storage_object(envelope)
# result.storage_object: ImmutableRawStorageObject, with
#   to_s3_metadata()["codestrata-client-type"] == "codestrata_cli"
# result.diagnostics: PartitionProjectionDiagnostics (client_type set, assessment_schema_version=None)
```

Order of checks, each raising `PartitionProjectionError` with a bounded,
allowlisted `code` (never raw exception text or payload fragments):

1. `stream_mismatch` — `envelope.event_stream` must be `"telemetry"`.
2. `unsupported_envelope_schema` / `unsupported_source_schema` /
   `unsupported_source_policy` — envelope/source identity must match the
   partition policy's supported sets.
3. `invalid_payload` — the payload must round-trip through
   `TelemetryIngestionRequest.model_validate()` (fail-closed typed
   re-check) — this also rejects a corrupted/unsupported `event_type`,
   since the model's own field validator enforces the
   `TelemetryEventType` allowlist.
4. `invalid_client_type` — `envelope.client.client_type` must be one of
   `TelemetryClientName`'s three members *and* must match the revalidated
   payload's `client.name` — both sides are checked independently so
   neither can be silently trusted alone.
5. `storage_object_invalid` — `build_immutable_raw_storage_object()` must
   succeed, and the resulting object (with the extra
   `codestrata-client-type` metadata attached) must itself validate.
6. `partition_invalid` — the resolved object key and S3 metadata must match
   the partition policy's generic dimensions and metadata allowlist.

This function **never calls a store** — it only resolves and validates a
`StorageProjectionResult`. Persistence is the caller's responsibility. There
is no `unsupported_assessment_schema` / `missing_assessment_schema` code
here — telemetry carries no nested "assessment schema" concept.

## Persisting a projection: `store_projected_telemetry`

```python
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    store_projected_telemetry,
)

write_result = store_projected_telemetry(store, projection)
```

Requires `store.put_immutable_storage_object(storage_object)` — the only
path that writes the *projected* object (including its
`codestrata-client-type` extra metadata) byte-exact, without rebuilding
from the envelope. Raises `AttributeError` for any store lacking it —
mirrors `store_projected_assessment_metadata` exactly (see
[assessment-metadata-data-lake.md](./assessment-metadata-data-lake.md#persisting-a-projection-store_projected_assessment_metadata)
for the full rationale, unchanged here).

Both stores already expose it (added in Slice 8.2 / Slice 8.4, unchanged by
this slice):

- `InMemoryCommunityDataLakeStore.put_immutable_storage_object()`
- `CommunityDataLakeS3Store.put_immutable_storage_object()`

## Privacy

- The object key carries only the five generic dimension names/values —
  never `client_type`, `event_type`, `event_id`, or `installation_id`.
- S3 metadata carries only the five generic keys plus the optional
  `codestrata-client-type` value (e.g. `"codestrata_cli"`) — never
  `event_type`, `occurred_at`, `properties`, `event_id`, or
  `installation_id`.
- `PartitionProjectionDiagnostics` carries `client_type` but structurally
  excludes `event_id`, `installation_id`, the object key, bucket, digest,
  payload, `event_type`, and `occurred_at` — see its fixed field list in
  [data-lake.md](./data-lake.md).
- `PartitionProjectionError.to_stable_dict()` returns only `{"code": ...,
  "detail": ...}` with `detail` bounded to 64 characters — never the
  original exception text or payload.

See `platform/tests/community_cloud_api/data_lake/test_telemetry_partition_privacy.py`.

## Testing

```bash
.venv/bin/pytest platform/tests/community_cloud_api/data_lake -q
.venv/bin/pytest platform/tests/community_cloud_api -q
```

New Slice 8.5 test modules:

- `test_telemetry_partition_policy.py` — `default_telemetry_partition_policy()`'s
  exact shape (generic `StreamPartitionPolicy` construction/validation is
  already covered by the Slice 8.4 test module).
- `test_telemetry_partitioning.py` — `project_telemetry_storage_object()`
  happy paths (including all three `TelemetryClientName` values) and every
  `PartitionProjectionError` code.
- `test_telemetry_partition_privacy.py` — object key, S3 metadata, and
  diagnostics never carry forbidden field values or keys; `client_type` is
  the only extra metadata key present.
- `test_telemetry_storage_projection.py` — end-to-end request → envelope →
  projection → in-memory store and fake-S3 store integration (`STORED` /
  `ALREADY_EXISTS` / `CONFLICT`), including `put_immutable_event()` alone
  dropping the extra metadata.
- `test_telemetry_partition_determinism.py` — repeated projection is
  byte-identical; different event keys/dates produce different
  keys/prefixes deterministically; `occurred_at` in the payload never
  affects the partition date.
- `test_telemetry_partition_compatibility.py` — every version stays pinned;
  the two partition policies (`telemetry`, `assessment_metadata`) remain
  distinct.
- `test_telemetry_partition_boundary.py` — no production wiring file (or
  the telemetry endpoint's own `routes.py`/`service.py`/`ports.py`)
  references any Slice 8.5 symbol or `data_lake` at all; telemetry-specific
  partition-key rejection paths (`client_type=`/`event_type=` as an extra
  dimension, stream/date mismatches).

`test_assessment_metadata_partition_privacy.py` and every other Slice 8.4
test continue to pass unchanged — `client_type` on
`PartitionProjectionDiagnostics` is optional and defaults to `None`.

## Limitations (Slice 8.5)

- No endpoint → storage wiring (still Slice 8.1–8.4's posture)
- No partition policy yet for `ai_usage` at the time of this slice;
  `cli_event`, `extension_event`, and `ai_usage` received theirs in
  Slices 8.6 / 8.7 / [8.8](./ai-usage-data-lake.md)
- No extra partition path dimension for this stream — `client_type` and
  `event_type` both remain outside the path (see dimension decision above);
  `event_type` additionally never appears in S3 metadata
- `occurred_at` is client-submitted content and never participates in the
  partition date — only the server-assigned acceptance date does
- No durable event-identity/deduplication store
- No OpenTofu / IAM change

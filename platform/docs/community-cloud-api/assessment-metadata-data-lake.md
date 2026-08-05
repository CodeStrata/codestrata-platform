# Assessment Metadata Partitioning (Slice 8.4)

Slice 8.4 gives the `assessment_metadata` event stream its own versioned
**partition policy** and a stream-specific **storage-object projector**,
built on top of the Slice 8.1–8.3 Community Data Lake foundation. It is the
first slice in Epic 8 where a single stream owns an explicit partition
contract rather than relying only on the generic Slice 8.1 Hive-style key
builder.

See [data-lake.md](./data-lake.md) (Slice 8.1 foundation),
[immutable-raw-storage.md](./immutable-raw-storage.md) (Slice 8.2 storage
contract), and [data-lake-event-envelope.md](./data-lake-event-envelope.md)
(Slice 8.3 envelope/registry) for what this slice builds on.

## What this slice does NOT do

- **Does not wire any endpoint to S3.** `app.py`, `deployment/wiring.py`,
  `deployment/settings.py`, and every endpoint service are unchanged — see
  `platform/tests/community_cloud_api/data_lake/test_assessment_metadata_partition_boundary.py`.
- **Does not start Slice 8.5+.** This slice stops at `assessment_metadata`
  plus the generic machinery. Later slices add partition policies for
  `telemetry` (8.5), `cli_event` (8.6), and `extension_event` (8.7);
  `ai_usage` followed in [Slice 8.8](./ai-usage-data-lake.md).
- **Does not bump any schema version.** Envelope schema, assessment metadata
  endpoint schema, and the Engine assessment report schema all stay `1.0`
  / `1.0` / `1.2` respectively. Only the **new** partition policy is
  versioned, at `1.0`.
- **Does not commit, plan, or apply any OpenTofu change.**
- **Does not add a durable event-identity/deduplication store.**

## Partition dimension decision

**Decision: retain the generic Hive path only.**

```text
raw/stream=assessment_metadata/schema_version=1.0/year=YYYY/month=MM/day=DD/{opaque}.json
```

No dimension is added for `client_type`, `assessment_status`,
`execution_result`, `assessment_schema_version`, `language`, `executed_heads`,
or `repository_shape`. Rationale:

- **Low operational need.** No analytics/Athena/dashboard consumer exists in
  this repository yet that would benefit from a finer-grained partition on
  any of these fields.
- **Avoid cardinality blow-up.** Several candidates (`executed_heads`
  combinations, `primary_language`, `repository_shape`) are effectively
  unbounded or high-cardinality relative to the fixed five-dimension generic
  path every stream already uses.
- **Cross-stream path consistency.** Keeping every stream's accepted path at
  exactly `stream=` / `schema_version=` / `year=` / `month=` / `day=`
  simplifies any future shared Glue/Athena catalog definition across all
  five streams.
- **Avoid identity fingerprinting.** Low-cardinality-per-repository
  attributes (language, shape, executed-head combination) become more
  re-identifying once combined with acceptance date and per-prefix object
  count. Keeping them private-payload-only (never in the key) avoids this
  risk entirely.

The Engine assessment report contract version (`assessment_schema_version`,
currently `"1.2"`) is instead surfaced as an **optional S3 metadata key**
(`codestrata-assessment-schema`) — informational only, never part of the
partition path.

## New generic (stream-agnostic) machinery

```text
platform/src/codestrata_platform/community_cloud_api/data_lake/
  partition_policies.py    # StreamPartitionPolicy — versioned per-stream partition contract
  stream_partitions.py       # object-key-vs-policy validation (stream-agnostic)
  partition_diagnostics.py     # PartitionProjectionDiagnostics — bounded, privacy-safe
  stream_storage.py              # StorageProjectionResult + merge_extra_s3_metadata()
  streams/
    assessment_metadata_partitioning.py   # the one concrete Slice 8.4 policy + projector
```

None of these modules know about any specific stream's payload shape except
`streams/assessment_metadata_partitioning.py`, which is the only module
importing `codestrata_platform.community_cloud_api.assessment_metadata.*`.

### `StreamPartitionPolicy`

A frozen, versioned dataclass (`partition_policies.py`) declaring, per
stream: supported envelope/source/assessment schema versions, the required
and optional Hive path dimensions, `max_partition_depth` /
`max_key_length` bounds, the S3 metadata allowlist, and
`forbidden_partition_fields` — field names that must never become a
partition dimension. `required_path_dimensions` is fixed at exactly the
generic five-dimension set (`stream`, `schema_version`, `year`, `month`,
`day`) in this slice — a policy cannot be constructed with any other
required-dimension set or a non-empty `optional_path_dimensions`, which
bakes the "generic path only" decision above into the type itself.

### `stream_partitions.py`

Stream-agnostic helpers used by every partition projector:

- `parse_hive_dimensions(object_key)` — parses the `key=value` segments
  between the root prefix and filename into an ordered mapping.
- `assert_partition_bounds(object_key, policy)` — key-length and
  dimension-count checks.
- `assert_partition_dimensions_allowed(object_key, policy)` — every
  required dimension present, no unlisted or forbidden dimension present.
- `assert_partition_key_matches_policy(object_key, policy, envelope)` — the
  full check: identity-material exclusion (delegates to
  `partitions.assert_key_excludes_identity_material`), accepted-root-prefix
  check, bounds, dimension allowlist, and cross-checks the `stream=`,
  `schema_version=`, and `year=`/`month=`/`day=` dimension values against
  the envelope that produced the key.
- `assert_s3_metadata_matches_policy(metadata, policy)` — every metadata key
  must be in `policy.s3_metadata_allowlist`.

All raise `StreamPartitionError` (a `ValueError` subclass distinct from
`PartitionPolicyError` — a malformed *policy* — and `PartitionKeyError` — a
malformed *key* independent of any policy).

### `PartitionProjectionDiagnostics`

A frozen, fixed-shape dataclass (`partition_diagnostics.py`) — the *only*
diagnostic surface a projector may return. Allowed fields: `event_stream`,
`envelope_schema_version`, `source_schema_version`,
`assessment_schema_version` (optional), `partition_policy_version`,
`partition_valid`, `projection_status`, `safe_event_reference`,
`safe_object_reference`, `limitations`. It structurally **cannot** carry
`event_id`, `installation_id`, the object key, bucket name, content digest,
payload fragments, counts, executed heads, or language — those fields do
not exist on the dataclass at all.

### `StorageProjectionResult`

`stream_storage.py` defines the return shape every projector produces:
`storage_object: ImmutableRawStorageObject` plus
`diagnostics: PartitionProjectionDiagnostics`. `merge_extra_s3_metadata()`
is a thin, generic wrapper that returns a `dataclasses.replace()`d copy of a
storage object with extra allowlisted S3 metadata attached, re-validating
and re-deriving metadata once so any not-allowlisted key fails closed at
merge time.

## The assessment metadata partition policy

```python
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    default_assessment_metadata_partition_policy,
)

policy = default_assessment_metadata_partition_policy()
policy.policy_token  # "community-assessment-metadata-partition-policy:1.0"
```

| Field | Value |
| --- | --- |
| `policy_id` | `community-assessment-metadata-partition-policy` |
| `policy_version` | `1.0` |
| `event_stream` | `assessment_metadata` |
| `supported_envelope_schema_versions` | `{"1.0"}` |
| `supported_source_schema_versions` | `{"1.0"}` |
| `supported_source_policy_ids` | `{"community-assessment-metadata-policy:1.0"}` |
| `supported_assessment_schema_versions` | `{"1.2"}` (kept in sync with `assessment_metadata.policy.ALLOWED_ASSESSMENT_SCHEMA_VERSIONS`) |
| `required_path_dimensions` | `("stream", "schema_version", "year", "month", "day")` |
| `optional_path_dimensions` | `()` |
| `s3_metadata_allowlist` | the 5 generic keys + `codestrata-assessment-schema` |
| `forbidden_partition_fields` | `event_id`, `installation_id`, `repository_name`, `repository_url`, `language`, `primary_language`, `repository_shape`, `executed_heads`, `finding_count`, `client_type`, `assessment_status`, `assessment_mode`, `assessment_schema_version`, `result`, `duration_bucket` |

## `project_assessment_metadata_storage_object`

```python
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    project_assessment_metadata_storage_object,
)

result = project_assessment_metadata_storage_object(envelope)
# result.storage_object: ImmutableRawStorageObject, with
#   to_s3_metadata()["codestrata-assessment-schema"] == "1.2"
# result.diagnostics: PartitionProjectionDiagnostics
```

Order of checks, each raising `PartitionProjectionError` with a bounded,
allowlisted `code` (never raw exception text or payload fragments):

1. `stream_mismatch` — `envelope.event_stream` must be `"assessment_metadata"`.
2. `unsupported_envelope_schema` / `unsupported_source_schema` /
   `unsupported_source_policy` — envelope/source identity must match the
   partition policy's supported sets.
3. `missing_assessment_schema` / `unsupported_assessment_schema` —
   `payload["assessment"]["assessment_schema_version"]` must be present and
   allowlisted.
4. `invalid_payload` — the payload must still round-trip through
   `AssessmentMetadataRequest.model_validate()` (fail-closed typed
   re-check, mirroring `envelope_validation.revalidate_payload_against_source_contract`).
5. `storage_object_invalid` — `build_immutable_raw_storage_object()` must
   succeed, and the resulting object (with the extra
   `codestrata-assessment-schema` metadata attached) must itself validate.
6. `partition_invalid` — the resolved object key and S3 metadata must match
   the partition policy's generic dimensions and metadata allowlist.

This function **never calls a store** — it only resolves and validates a
`StorageProjectionResult`. Persistence is the caller's responsibility.

## Why `codestrata-assessment-schema` needs `extra_s3_metadata`

Attaching a stream-specific metadata key *after*
`build_immutable_raw_storage_object()` runs would be silently lost if a
caller later persisted via `store.put_immutable_event(envelope)` — that path
rebuilds the storage object from the envelope alone and never sees the
projector's extra metadata. Slice 8.4 closes this gap generically:

1. `ImmutableRawStorageObject` gains an optional
   `extra_s3_metadata: tuple[tuple[str, str], ...] = ()` field (a tuple of
   pairs, not a `Mapping`, so the frozen/slotted dataclass stays hashable).
2. `to_s3_metadata()` merges the five base keys with `extra_s3_metadata`,
   still validating every resulting key against `ALLOWED_S3_METADATA_KEYS`
   and rejecting any attempt to override a base key.
3. `ALLOWED_S3_METADATA_KEYS` gains one new optional key:
   `codestrata-assessment-schema` (the Engine assessment report contract
   version — never the endpoint/envelope schema version).
4. `project_assessment_metadata_storage_object()` builds the base object via
   `build_immutable_raw_storage_object()`, then returns a
   `merge_extra_s3_metadata()`-derived copy carrying
   `{"codestrata-assessment-schema": assessment_schema_version}`.
5. **Persistence must use `put_immutable_storage_object`, not
   `put_immutable_event`**, to durably carry this extra metadata — see
   below.

## Persisting a projection: `store_projected_assessment_metadata`

```python
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    store_projected_assessment_metadata,
)

write_result = store_projected_assessment_metadata(store, projection)
```

Requires `store.put_immutable_storage_object(storage_object)` — the only
path that writes the *projected* object (including its extra metadata)
byte-exact, without rebuilding from the envelope. Raises `AttributeError`
for any store lacking it; there is no correct fallback to
`put_immutable_event()` alone, since that path would silently drop the
projector's extra metadata.

Both stores now expose it:

- `InMemoryCommunityDataLakeStore.put_immutable_storage_object()` — added in
  Slice 8.2, unchanged.
- `CommunityDataLakeS3Store.put_immutable_storage_object()` — **new in
  Slice 8.4**. Skips `build_immutable_raw_storage_object()` entirely and
  writes the given object's bytes/key/metadata directly through the same
  `IfNoneMatch: "*"` conditional-write / `PreconditionFailed` →
  `head_object` resolution path `put_immutable_event()` already uses.
  `put_immutable_event()` itself is unchanged — it still rebuilds from the
  envelope and therefore never carries stream-specific extra metadata.

## Privacy

- The object key carries only the five generic dimension names/values —
  never `client_type`, `assessment_status`, `primary_language`,
  `repository_shape`, `executed_heads`, `event_id`, or `installation_id`.
- S3 metadata carries only the five generic keys plus the optional
  `codestrata-assessment-schema` value (e.g. `"1.2"`) — never any payload
  fragment, count, or identity material.
- `PartitionProjectionDiagnostics` structurally excludes `event_id`,
  `installation_id`, the object key, bucket, digest, payload, counts, heads,
  and language — see its fixed field list above.
- `PartitionProjectionError.to_stable_dict()` returns only `{"code": ...,
  "detail": ...}` with `detail` bounded to 64 characters — never the
  original exception text or payload.

See `platform/tests/community_cloud_api/data_lake/test_assessment_metadata_partition_privacy.py`.

## Testing

```bash
.venv/bin/pytest platform/tests/community_cloud_api/data_lake -q
.venv/bin/pytest platform/tests/community_cloud_api -q
```

New Slice 8.4 test modules:

- `test_assessment_metadata_partition_policy.py` — generic
  `StreamPartitionPolicy` construction/validation plus the default
  assessment policy's exact shape.
- `test_assessment_metadata_partitioning.py` — `extract_assessment_schema_version()`
  and `project_assessment_metadata_storage_object()` happy paths and every
  `PartitionProjectionError` code.
- `test_assessment_metadata_partition_privacy.py` — object key, S3 metadata,
  and diagnostics never carry forbidden field values or keys.
- `test_assessment_metadata_storage_projection.py` — end-to-end request →
  envelope → projection → in-memory store and fake-S3 store integration
  (`STORED` / `ALREADY_EXISTS` / `CONFLICT`), including
  `put_immutable_event()` alone dropping the extra metadata (documenting why
  `put_immutable_storage_object` is required).
- `test_assessment_metadata_partition_determinism.py` — repeated projection
  is byte-identical; different event keys/dates produce different
  keys/prefixes deterministically.
- `test_assessment_metadata_partition_compatibility.py` — every version stays
  pinned; the partition policy's assessment-schema allowlist stays in sync
  with the endpoint policy's.
- `test_assessment_metadata_partition_boundary.py` — no production wiring
  file references any Slice 8.4 symbol; low-level `stream_partitions.py`
  rejection paths (malformed segments, extra/forbidden dimensions,
  quarantine-prefix rejection, date/stream/schema mismatches).

## Limitations (Slice 8.4)

- No endpoint → storage wiring (still Slice 8.1–8.3's posture)
- No partition policy yet for `ai_usage` at the time of this slice; later
  slices added policies for `telemetry` (8.5), `cli_event` (8.6),
  `extension_event` (8.7), and `ai_usage`
  ([8.8](./ai-usage-data-lake.md))
- No extra partition path dimension for this stream — `client_type`,
  `assessment_status`, execution result, assessment schema version,
  language, executed heads, and repository shape all remain private-payload
  only (see dimension decision above)
- No durable event-identity/deduplication store
- No OpenTofu / IAM change

# Immutable Raw JSON Storage Contract (Slice 8.2)

Slice 8.2 adds the **immutable raw-JSON storage contract** on top of the
Slice 8.1 Community Data Lake domain foundation: canonical byte-exact JSON
serialization, a fully-resolved storage object model, fail-closed
existing-object conflict classification, privacy-safe write receipts, and a
production-capable (but **unwired**) S3 adapter.

See [data-lake.md](./data-lake.md) for the Slice 8.1 foundation this slice
builds on (policy, envelope, identity, partitions, event streams).

**Slice 8.3** (later) evolves the envelope this contract serializes from a
flat shape to a nested `acceptance` / `client` / `identity` /
`source_contract` shape — still envelope schema `1.0` — and adds a typed
per-stream registry/builder layer. Everything in this document
(`canonical_json`, `ImmutableRawStorageObject`, `decisions`, `receipts`, the
S3 adapter) is unchanged in behavior: `serialize_canonical_raw_json()` still
serializes whatever `envelope.to_stable_dict()` returns, whatever its
internal shape. See
[data-lake-event-envelope.md](./data-lake-event-envelope.md).

## What this slice does NOT do

- **Does not wire any endpoint to S3.** `app.py`, `deployment/wiring.py`,
  `deployment/settings.py`, and every endpoint service are unchanged.
- **Does not claim exactly-once delivery anywhere.** Conditional writes
  (`IfNoneMatch: "*"`) make concurrent writers safe against clobbering a
  differently-keyed object, not delivery exactly-once. A retried `PutObject`
  after a transient failure, or a caller retry after a
  received-but-unacknowledged response, may both legitimately resolve to
  `ALREADY_EXISTS`. Every `StorageReceipt` discloses this via its
  `limitations` field.
- **Does not define any new HTTP contract.** No `202 Accepted`, no new
  request/response schema — this slice is storage-layer only.
- **Quarantine persistence is Slice 8.9.** Slice 8.2 deferred
  `quarantine_event`; Slice 8.9 implements projection + conditional S3
  writes under `quarantine/` (still unwired from endpoints). See
  [data-lake-quarantine.md](./data-lake-quarantine.md).
- **Retention / lifecycle product policy is Slice 8.10** (accepted vs
  quarantine expiry, multipart abort, delete-marker cleanup,
  `force_destroy=false`). Immutability during the retention window is
  unchanged: writers still Deny-delete on `raw/*`. See
  [data-lake-retention.md](./data-lake-retention.md).
- **Encryption at rest is Slice 8.11** (SSE-S3 / AES256 bucket default +
  explicit Put headers; KMS deferred). Encryption protects confidentiality
  at rest; it does not replace conditional-write immutability. See
  [data-lake-encryption.md](./data-lake-encryption.md).
- **Restricted IAM access is Slice 8.12** (least-privilege writer policy
  document, Put/Get only via adapter, delete Deny, no ListBucket, writer
  unattached). See [data-lake-access-control.md](./data-lake-access-control.md).
- **Storage abstraction is Slice 8.13** (typed projected-object port, explicit
  factory, production-default unavailable adapter, stream `store_projected_*`
  requires `put_immutable_storage_object`). See
  [data-lake-storage-abstraction.md](./data-lake-storage-abstraction.md).
- **Does not change any version.** Data Lake policy stays `1.0`, envelope
  schema stays `1.0`.
- **Does not commit, plan, or apply any OpenTofu change** for this slice's
  code (see [IAM](#iam-no-change-needed) below).

## Package layout

```text
platform/src/codestrata_platform/community_cloud_api/data_lake/
  canonical_json.py      # storage-authority canonical JSON serialization
  objects.py              # ImmutableRawStorageObject (resolved, storage-ready)
  receipts.py              # StorageReceipt (privacy-safe write outcome)
  decisions.py              # fail-closed existing-object conflict classification
  immutable_write.py         # build_immutable_raw_storage_object(envelope, policy)
  errors.py                   # StorageErrorCategory / DataLakeStorageError

  infrastructure/              # THE ONLY subpackage allowed to import boto3
    __init__.py
    s3_store.py                 # CommunityDataLakeS3Store — production-capable, unwired
    client.py                    # S3ClientPort + create_boto3_s3_client (lazy import)
    configuration.py               # S3DataLakeStoreConfiguration (no env reads)
    error_mapping.py                # map_s3_exception / is_transient_storage_error
    diagnostics.py                    # safe_s3_storage_diagnostic
```

Every module directly under `data_lake/` (the domain) remains `boto3`-free —
enforced by `platform/tests/community_cloud_api/data_lake/test_boundary.py`.
Only `data_lake/infrastructure/client.py` imports `boto3`, and only lazily
inside `create_boto3_s3_client`'s function body.

## Canonical raw JSON (storage authority)

`canonical_json.serialize_canonical_raw_json(envelope)` produces the exact
immutable bytes written to storage:

- `envelope.to_stable_dict()` → sorted-map JSON, `sort_keys=True`,
  `separators=(",", ":")`, `ensure_ascii=True`, `allow_nan=False`.
- UTF-8 encoded, **no trailing newline** — this differs deliberately from
  the HTTP `serialization.dumps_stable()` helper, whose trailing `\n` is a
  wire-format convenience, not part of the durable object identity.
- `content_sha256 = "sha256:" + sha256(bytes).hexdigest()` is the object's
  content-identity digest, carried in S3 metadata and in every
  `StorageReceipt`.
- List order is preserved; only map keys are sorted.
- NaN/Infinity floats are rejected (`CanonicalJsonError`), matching the HTTP
  serialization boundary's own rejection rule.

## Immutable storage object

`immutable_write.build_immutable_raw_storage_object(envelope, policy)`
composes the Slice 8.1 identity/partition/policy modules with canonical JSON
serialization into an `ImmutableRawStorageObject`: canonical bytes, digest,
length, the Hive-style `raw/...json` key, and only the **allowlisted** S3
metadata keys:

| Metadata key | Value |
| --- | --- |
| `codestrata-content-sha256` | Full `sha256:<hex>` digest |
| `codestrata-envelope-schema` | Envelope schema version (`1.0`) |
| `codestrata-source-schema` | Source endpoint schema version |
| `codestrata-stream` | Event stream (e.g. `telemetry`) |
| `codestrata-object-id` | Opaque hex fragment only — **no** `lake-object:` prefix |
| `codestrata-assessment-schema` *(optional, Slice 8.4)* | Engine assessment report contract version (e.g. `1.2`) — only ever attached by the `assessment_metadata` stream's projector, never the endpoint/envelope schema version |
| `codestrata-client-type` *(optional, Slice 8.5 / 8.7 / 8.8)* | Client-type classification — attached by the `telemetry` projector (`codestrata_cli` / `vscode_extension` / `other_extension`), by the `extension_event` projector (`vscode_extension` active; `cursor_extension` historical-only), and by the `ai_usage` projector (`codestrata_cli` / `vscode_extension` active; `cursor_extension` historical-only); never `event_type`, `editor`, `operation`, `capability`, `provider_family`, or `model_family` |

The `cli_event` stream (Slice 8.6) adds **no** new metadata key at all — its
partition policy's `s3_metadata_allowlist` is exactly the five base keys
above (`BASE_S3_METADATA_KEYS`, now exported publicly from this module), and
its projector never calls `merge_extra_s3_metadata()`. See
[cli-event-data-lake.md](./cli-event-data-lake.md) for the rationale
(the CLI client is always `codestrata_cli` — a constant value carries no
metadata information — and `operation`/`lifecycle`/`result` stay
private-payload-only).

The `extension_event` stream (Slice 8.7) reuses `codestrata-client-type`
(Option B) for `vscode_extension` (active) / historical `cursor_extension` — never `editor` or
`operation` in metadata. See
[extension-event-data-lake.md](./extension-event-data-lake.md).

The `ai_usage` stream (Slice 8.8) reuses `codestrata-client-type`
(Option B) for `codestrata_cli` / `vscode_extension` (active) / historical `cursor_extension` —
never `capability`, `provider_family`, or `model_family` in metadata. See
[ai-usage-data-lake.md](./ai-usage-data-lake.md).

No other metadata key is ever written. `event_key`, `safe_event_reference`,
request IDs, and IP addresses never appear in metadata or in the object key
— `ImmutableRawStorageObject.validate()` and `to_s3_metadata()` both enforce
this structurally, independent of the Slice 8.1 key-builder's own checks.

**Slice 8.4** adds an optional `extra_s3_metadata: tuple[tuple[str, str],
...]` field (default `()`) so a stream-specific projector can attach
additional, still-allowlisted metadata without changing
`build_immutable_raw_storage_object()` itself. `to_s3_metadata()` merges the
five base keys above with `extra_s3_metadata`, rejects any attempt to
override a base key, and still enforces `ALLOWED_S3_METADATA_KEYS` /
`FORBIDDEN_S3_METADATA_KEYS` on every resulting key. See
[assessment-metadata-data-lake.md](./assessment-metadata-data-lake.md) for
the concrete `codestrata-assessment-schema` use.

## Fail-closed existing-object classification

`decisions.classify_existing_object(requested_digest=..., stored_digest=...)`
governs every "object already exists at this key" decision, in both the
in-memory store and the S3 adapter:

| Stored digest | Outcome |
| --- | --- |
| Missing (`None`) | `CONFLICT` — **never** `ALREADY_EXISTS` |
| Malformed (not `sha256:` + 64 lowercase hex) | `CONFLICT` |
| Matches requested digest | `ALREADY_EXISTS` |
| Differs from requested digest | `CONFLICT` |

This is intentionally fail-closed: an S3 object whose digest metadata cannot
be read or parsed is always treated as a conflict, never silently accepted
as a replay.

## Storage receipts

`StorageReceipt` is the bounded, privacy-safe outcome of one write attempt:

- `to_public_dict()` — **never** includes `object_key`, bucket, ETag,
  version id, region, or account. Safe for any external caller (though no
  endpoint returns it in this slice).
- `to_internal_dict()` — superset that includes `object_key`, for
  service-layer code and tests only.
- `stored_object_reference` — opaque `"lake-ref:" + <first 16 hex chars of
  the object id>` — never the raw object key or bucket.
- `limitations` — always discloses
  `"no_exactly_once_delivery_guarantee"` and
  `"conditional_write_not_transactional_across_retries"`.

## The S3 adapter (production-capable, unwired)

`CommunityDataLakeS3Store` implements the same
`put_immutable_event` / `quarantine_event` port as
`InMemoryCommunityDataLakeStore`, backed by an injected `S3ClientPort`
(structurally satisfied by a real `boto3` S3 client):

1. Build the `ImmutableRawStorageObject`. Any validation failure →
   `REJECTED` before any S3 call is made.
2. `PutObject` with `Bucket`, `Key`, `Body` (canonical bytes), `ContentType:
   application/json`, `ContentLength`, **`IfNoneMatch: "*"`** (required,
   never omitted), the allowlisted `Metadata`, `ChecksumSHA256` (when
   `checksum_required`), and always `ServerSideEncryption: AES256` for
   `encryption_mode == "sse_s3"` (Slice 8.11; unsupported modes fail closed
   before AWS; no `SSEKMSKeyId`).
3. Success → `STORED` + `StorageReceipt`.
4. `PreconditionFailed` (412) → **exactly one** `head_object` call reads
   `Metadata[metadata_digest_key]` and resolves via
   `classify_existing_object` to `ALREADY_EXISTS` or `CONFLICT` — the
   adapter **never** retries `PutObject` after a precondition failure, so
   the existing object is never overwritten.
5. Transient errors (`SlowDown`, `ServiceUnavailable`, `InternalError`,
   `RequestTimeout`, `5xx`, connect/read timeouts) retry up to
   `config.max_attempts` times, then return `UNAVAILABLE`. No sleep-based
   backoff is used, so unit tests run instantly.
6. `AccessDenied` (403), checksum-mismatch codes (`BadDigest`,
   `InvalidDigest`), and any unrecognized error return `REJECTED` /
   `UNAVAILABLE` immediately — never retried.
7. **Slice 8.9:** `quarantine_event` projects a `QuarantineRecord` into an
   `ImmutableQuarantineStorageObject` and writes it with the same
   `IfNoneMatch: "*"` / precondition-resolution path, using
   quarantine-only S3 metadata. See
   [data-lake-quarantine.md](./data-lake-quarantine.md).

The adapter exposes `put_immutable_event` and `quarantine_event` — no
`delete`, `update`, or `list` method exists. **Slice 8.4** adds one more
method, `put_immutable_storage_object(storage_object)`, which writes an
already-resolved `ImmutableRawStorageObject` directly (validating it, then
reusing the same conditional-write / `PreconditionFailed` resolution path
as `put_immutable_event`) without rebuilding it from an envelope. This is
required for a stream-specific projector's `extra_s3_metadata` to be
persisted byte-exact — `put_immutable_event(envelope)` alone rebuilds the
object from the envelope and would silently drop it. See
[assessment-metadata-data-lake.md](./assessment-metadata-data-lake.md#persisting-a-projection-store_projected_assessment_metadata),
for the Slice 8.5 `telemetry` equivalent,
[telemetry-data-lake.md](./telemetry-data-lake.md#persisting-a-projection-store_projected_telemetry),
for the Slice 8.6 `cli_event` equivalent (which, unlike the other two,
carries no extra metadata to lose either way, but still uses
`put_immutable_storage_object` for cross-stream consistency),
[cli-event-data-lake.md](./cli-event-data-lake.md#persisting-a-projection-store_projected_cli_event),
for the Slice 8.7 `extension_event` equivalent (Option B client-type
metadata, same durability requirement as telemetry),
[extension-event-data-lake.md](./extension-event-data-lake.md#persisting-a-projection-store_projected_extension_event),
and for the Slice 8.8 `ai_usage` equivalent (Option B client-type
metadata, same durability requirement),
[ai-usage-data-lake.md](./ai-usage-data-lake.md#persisting-a-projection-store_projected_ai_usage).

### ETag is not the authority; conditional write is

S3's `ETag` is not treated as this contract's authority for content
identity — it is not even inspected. The digest carried in
`codestrata-content-sha256` metadata (verified by `content_sha256` on the
`ImmutableRawStorageObject`) is the sole content-identity signal this
package trusts. The conditional `IfNoneMatch: "*"` header is what actually
prevents two concurrent writers from clobbering each other's object; it is
not, by itself, an exactly-once delivery guarantee (see above).

## Configuration (no environment reads)

`S3DataLakeStoreConfiguration` is a pure, validated dataclass — it never
reads environment variables or files. Bucket names are validated
(lowercase alphanumeric/hyphen, 3–63 chars, no `s3://`, `/`, `:`, or
credential-like content); only `raw_prefix = "raw/"` and
`encryption_mode = "sse_s3"` are accepted in this slice; `endpoint_url`
(tests only, e.g. a local S3-compatible server) requires
`allow_endpoint_override=True`.

## Wiring status

| Component | Status |
| --- | --- |
| Domain modules (`canonical_json.py`, `objects.py`, `receipts.py`, `decisions.py`, `immutable_write.py`, `errors.py`) | Implemented, unit-tested, `boto3`-free |
| `infrastructure/` S3 adapter | Implemented, unit-tested with a fake S3 client, production-capable |
| `app.py` / `deployment/wiring.py` / `deployment/settings.py` | **Unchanged** — no reference to `data_lake` at all |
| Any endpoint service | **Unchanged** — no reference to `data_lake` or `infrastructure` |
| `create_boto3_s3_client` | Exists, never called by production wiring in this slice |

## IAM: no change needed

`HeadObject` (used exactly once per `PreconditionFailed` resolution) is
authorized by the `s3:GetObject` action, which the Slice 8.1 writer IAM
policy document already grants on both `raw/*` and `quarantine/*` (see
`infrastructure/modules/community-data-lake/iam.tf`). No OpenTofu change is
made or needed for this slice, and the writer policy remains **unattached**
to any Lambda, role, or user.

## Testing

```bash
.venv/bin/pytest platform/tests/community_cloud_api/data_lake -q
```

Covers: canonical serialization determinism and rejection rules, storage
object structural validation, receipt privacy boundaries, fail-closed
conflict classification, in-memory store parity with the byte-exact
contract, the S3 adapter's `STORED` / `ALREADY_EXISTS` / `CONFLICT` /
`UNAVAILABLE` / `REJECTED` outcomes against a fake S3 client, S3 exception
mapping, and adapter privacy (no bucket/key/AWS-message leakage anywhere).

## Limitations (Slice 8.2)

- No endpoint → storage wiring (still Slice 8.1's posture)
- No exactly-once delivery guarantee
- No quarantine persistence (adapter returns `REJECTED` for
  `quarantine_event`)
- No real-backoff/sleep retry (bounded attempt count only)
- No OpenTofu / IAM change
- No Slice 8.3 work of any kind

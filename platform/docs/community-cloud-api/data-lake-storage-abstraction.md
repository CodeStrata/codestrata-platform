# Community Data Lake Storage Abstraction (Slice 8.13)

Slice 8.13 formalizes the **storage-abstraction product-policy contract** and
the typed immutable storage **port** for the Community Data Lake. Platform
defines adapter-neutral intent, capability sets, factory modes, and
privacy-safe diagnostics. OpenTofu/IAM (Slices 8.1 / 8.12) and stream
projectors (Slices 8.4–8.8) remain separate; this slice does **not** wire
endpoints, attach the writer policy, or enable ingestion.

## Policy token

```text
community-data-lake-storage-policy:1.0
```

`CommunityDataLakeStoragePolicy` / `default_storage_policy()` capture:

- **Projected-object authority** — authoritative writes use
  `put_immutable_storage_object` / `put_immutable_quarantine_object` with
  fully resolved storage objects (stream-specific metadata preserved).
- **Separate accepted/quarantine methods** — no cross-namespace puts.
- **Envelope put is convenience only** — `put_immutable_event` rebuilds from
  the envelope and must not be used when stream projectors attach extra S3
  metadata.
- **No list/delete/update/admin surface** on the port.
- **Production default unavailable** — unwired deployments fail closed.
- **In-memory adapter is test-only** — never allowed in production composition.
- **Writer policy unattached** — IAM attachment deferred to Slice 8.15.

## Port design

`CommunityDataLakeStore` (Protocol in `ports.py`) requires:

| Method | Input | Purpose |
| --- | --- | --- |
| `put_immutable_storage_object` | `ImmutableRawStorageObject` | Accepted `raw/` writes |
| `put_immutable_quarantine_object` | `ImmutableQuarantineStorageObject` | Quarantine writes |
| `put_immutable_event` | `DataLakeEnvelope` | Convenience / tests only |
| `quarantine_event` | `QuarantineRecord` | Project + quarantine convenience |

Aliases: `put_accepted_object`, `put_quarantine_object`.

`StorageWriteResult` carries `status`, optional `storage_class`
(`accepted` | `quarantine`), receipts, and an internal `object_key`.
External serialization uses `to_public_dict()` / `storage_result_to_public_dict()`
— never includes bucket, key, ARN, ETag, or version ID.

## Projected-object authority

Every stream's `store_projected_*` helper calls
`store.put_immutable_storage_object(projection.storage_object)` directly — no
`getattr` fallback to `put_immutable_event`. Rebuilding from the envelope alone
would drop stream-specific extra S3 metadata (e.g.
`codestrata-assessment-schema`, `codestrata-client-type`) — a durability
defect this slice prevents.

## Adapters

| Adapter | Mode | Capabilities | Production use |
| --- | --- | --- | --- |
| `UnavailableCommunityDataLakeStore` | `unavailable` | `UNAVAILABLE` only | **Default** when unwired |
| `InMemoryCommunityDataLakeStore` | `in_memory_test` | Writes + conditional create + checksum | Tests only |
| `CommunityDataLakeS3Store` | `s3` | Writes + encryption + retry verify | Capable but unwired |

Capability sets live in `StorageCapabilities` / `StorageCapability`. Forbidden
capabilities (`list`, `delete`, `update`, `bucket_admin`, …) are rejected at
construction. `UNAVAILABLE` cannot combine with write capabilities.

## Factory

`create_community_data_lake_store(configuration, *, s3_config, s3_client, …)`:

- Never reads environment variables.
- Default: `DataLakeStorageConfiguration.unavailable()` → unavailable adapter.
- `in_memory_test` requires explicit `allow_in_memory_test=True`.
- `s3` requires validated `S3DataLakeStoreConfiguration` and either an injected
  client or lazy `boto3` import (ImportError → `StorageValidationError`).
- **Not** invoked by `app.py` or `deployment/wiring.py`.

## Configuration boundary

`DataLakeStorageConfiguration.to_stable_dict()` exposes mode flags only — never
bucket names, prefixes, endpoints, or credentials.

`S3DataLakeStoreConfiguration` (infrastructure) validates:

- Bucket name (lowercase, 3–63, no `s3://`, `/`, `:`, `@`)
- Fixed prefixes: `raw/`, `quarantine/` (collision guarded)
- Encryption: `sse_s3` only (no KMS key)
- `endpoint_url` requires `allow_endpoint_override=True` (tests only)

## Transaction limitation

There is **no transaction** across event-identity coordination and storage.
Identity classification and immutable writes are separate steps with no
exactly-once claim. Limitations include
`no_transaction_across_identity_and_storage` and
`no_durable_event_identity_coordination`.

## IAM: Put/Get only

Slice 8.12 defines writer IAM intent: prefix-scoped `s3:PutObject` and
`s3:GetObject` (HeadObject retry classification), delete Deny, no
ListBucket, no KMS IAM. Slice 8.13 reconciles the storage port and adapters
with that contract — adapters call `put_object` and `head_object` only.
Static tests assert `iam.tf` unchanged regarding ListBucket.

## Error taxonomy

Canonical safe codes in `storage_errors.py` reconcile with
`StorageErrorCategory` and S3 mapping (`map_s3_exception`). Access denied maps
to `REJECTED` + `storage_access_denied`, not `STORED`. Transient errors map to
`UNAVAILABLE`.

## Diagnostics

`StorageAbstractionDiagnostics` / `diagnostics_from_storage()` produce
deterministic, privacy-safe dumps: policy version, adapter type, capability
names, encryption mode category, validation status, limitations. Never includes
bucket, prefix, endpoint, key, or ARN.

## Unwired posture

- No `app.py` / `deployment/wiring.py` / endpoint imports of storage factory
  or data lake modules.
- Engine remains unaware of the data lake.
- Production default adapter is **unavailable** — no false `STORED`.
- Writer IAM remains **unattached**; `enable_ingestion_wire = false`.
- No claim that production data is stored.

## Relationship to Slice 8.14 / 8.15

**Slice 8.14** (integration verification) is **complete**: end-to-end checks
for all five streams and quarantine across in-memory and fake-S3 adapters,
storage factory modes, privacy, retention/encryption/access reconciliation,
and static infrastructure contract — without wiring ingestion.

**Slice 8.15** (Epic 8 completion verification) is **complete**: boundary and
completion checks (package inventory, ownership boundaries, version registry,
production fail-closed posture) reusing the SV.9 integration report — it does
**not** wire ingestion, attach writer IAM, or enable production storage.

**Epic 8 is complete.** Production ingestion is **not operational**. **Epic 9
is not started.**

| Slice | Concern |
| --- | --- |
| 8.1–8.3 | Bucket, envelope, identity foundation |
| 8.4–8.8 | Stream partition projectors + `store_projected_*` |
| 8.9 | Quarantine port |
| 8.10 | Retention / lifecycle |
| 8.11 | SSE-S3 encryption |
| 8.12 | Least-privilege IAM intent |
| **8.13** | **Storage abstraction policy, port, factory, adapters** |
| **8.14** | **Integration verification (SV.9 data lake package)** |
| **8.15** | **Epic 8 completion verification (boundary + completion report)** |

## Package symbols

```text
community-data-lake-storage-policy:1.0
CommunityDataLakeStoragePolicy / default_storage_policy()
StorageCapabilities / StorageCapability / FORBIDDEN_STORAGE_CAPABILITIES
DataLakeStorageConfiguration / StorageAdapterType
create_community_data_lake_store()
StorageAbstractionDiagnostics / diagnostics_from_storage()
StorageValidationError / validate_storage_policy_invariants()
assert_accepted_storage_object() / assert_quarantine_storage_object()
storage_result_to_public_dict() / ALLOWED_STORAGE_WRITE_STATUSES
CANONICAL_STORAGE_SAFE_CODES / STORAGE_* safe-code constants
```

See also: [data-lake.md](./data-lake.md),
[immutable-raw-storage.md](./immutable-raw-storage.md),
[data-lake-quarantine.md](./data-lake-quarantine.md),
[data-lake-access-control.md](./data-lake-access-control.md),
[data-lake-encryption.md](./data-lake-encryption.md),
[data-lake-retention.md](./data-lake-retention.md),
`infrastructure/docs/community-data-lake.md`.

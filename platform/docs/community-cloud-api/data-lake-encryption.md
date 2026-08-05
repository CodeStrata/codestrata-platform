# Community Data Lake Encryption at Rest (Slice 8.11)

Slice 8.11 formalizes the **encryption-at-rest product-policy contract** for the
Community Data Lake: Platform
`community-data-lake-encryption-policy:1.0` aligned with OpenTofu
`encryption.tf` (SSE-S3 / AES256) and the S3 adapter's explicit
`ServerSideEncryption=AES256` PutObject headers.

This slice does **not** claim that production Community events are stored.
Endpoints, `app.py`, and `deployment/wiring.py` remain unwired from the data
lake. `enable_ingestion_wire` stays `false`. Customer-managed KMS is **not**
enabled.

## SSE-S3 decision (v0.2.0)

**Operational mode:** `sse_s3` only (`AES256`).

| Benefits | Limitations |
| --- | --- |
| Encryption at rest by default | No customer-managed key |
| Low operational complexity | Less granular key-level IAM |
| No key-policy administration | No independent KMS audit boundary |
| No KMS request cost | Future cross-account analytics may need migration |
| No key alias / ARN exposure | Relies on S3-managed keys |
| Simple infrastructure extraction | |

`sse_kms` exists in the `EncryptionMode` enum for forward documentation only.
It is **not** operational: Platform policy, OpenTofu validation, and adapter
configuration all reject it.

## Defense in depth: bucket default + Put headers

1. **Bucket default encryption** — OpenTofu
   `aws_s3_bucket_server_side_encryption_configuration` with
   `sse_algorithm = "AES256"` and `bucket_key_enabled = false` (S3 Bucket Keys
   are an SSE-KMS cost feature and must not imply a KMS posture under SSE-S3).
2. **Explicit PutObject headers** — `CommunityDataLakeS3Store._put_object`
   always sets `ServerSideEncryption=AES256` for accepted and quarantine
   writes; never omits encryption; never sends `SSEKMSKeyId`.

Together these protect against a future internal writer that forgets headers
(bucket default still encrypts) and reconcile Platform configuration with
infrastructure.

## Bucket-policy Deny limitation

**v0.2.0 does not** add a broad bucket-policy `Deny` for missing or incorrect
`x-amz-server-side-encryption` headers (e.g. `DenyUnencryptedObjectUploads`).

Rationale: AWS condition complexity, risk to lifecycle / service-generated
writes, and operational testing cost outweigh the benefit for this foundation
slice. Documented limitation code:
`no_bucket_policy_deny_unencrypted_writes`.

Defense in depth for product writers remains: bucket default + adapter
headers. A future hardening slice may add a carefully scoped Deny.

## Accepted / quarantine parity

Both `raw/` (accepted) and `quarantine/` share:

- the same encrypted bucket
- the same SSE-S3 default
- the same adapter `_put_object` path (`ServerSideEncryption=AES256`)

There is no weaker quarantine encryption path and no unencrypted fallback.

## Checksum vs encryption

| Concern | Responsibility |
| --- | --- |
| Content digest (`sha256:…`) | Canonical plaintext JSON identity |
| S3 `ChecksumSHA256` | Transport / content integrity on Put |
| SSE-S3 | Confidentiality of bytes **at rest** in S3 |
| ETag | Not the content authority |

Encryption does **not** change the logical content digest, does **not**
participate in object / event identity, and must not hash ciphertext. The
application stores canonical plaintext bytes over TLS; S3 performs
server-side encryption.

## Immutability vs encryption

| Control | Role |
| --- | --- |
| Conditional `IfNoneMatch="*"` | Prevents overwrite (immutability) |
| SSE-S3 | Protects bytes at rest (confidentiality) |
| Versioning | Recovery / noncurrent lifecycle |
| Writer IAM Deny delete on `raw/*` | Restricts writers |
| Lifecycle expiry | Retention (Slice 8.10) |

Encryption does not provide immutability. Immutability does not provide
confidentiality.

## KMS deferred

Design review only — **no** `aws_kms_key`, alias, grant, KMS IAM actions,
key ARN outputs, or key ID environment variables in this slice.

Future migration (when release-owner approved) would need dedicated key,
rotation, restricted key policy, ingest encrypt / analytics decrypt
separation, alias strategy, deletion window, and extraction impact. Until
then, treating KMS as half-enabled is a defect.

## No key identifiers in product contracts

Encryption key identifiers must never appear in Community API responses,
public storage receipts, structured logs, envelopes, S3 object metadata,
Engine/CLI/extension packages, or public export. For SSE-S3 there is no
customer-managed key ID. Diagnostics may report `encryption_mode` and
`kms_enabled=false` but never bucket/key/account identifiers.

OpenTofu `encryption_mode` output is the **mode string** (`sse_s3`) only —
not a key id.

## Failure behavior

| Condition | Outcome |
| --- | --- |
| Unsupported `encryption_mode` | Rejected before AWS (`S3ConfigurationError` / policy validation) |
| Config mutated away from `sse_s3` | `_put_object` fail-closed (`StorageObjectError`) |
| Unexpected `KMS.*` AWS codes | `storage_encryption_failed` (REJECTED) — not conflict / exact-retry |
| Encryption misconfiguration | Never fall back to unencrypted Put; never retry with encryption removed |

Safe codes never include bucket names, object keys, AWS request IDs, or raw
service text.

## In-memory store

`InMemoryCommunityDataLakeStore` models contract behavior only. It does
**not** cryptographically encrypt bytes. Limitation:
`in_memory_store_does_not_cryptographically_encrypt`.

## Unwired posture

- No `app.py` / `wiring.py` / endpoint imports of encryption or data lake
- Writer IAM remains unattached; `enable_ingestion_wire = false`
- Engine remains unaware of the data lake
- No claim that production data is stored

Platform references infrastructure defaults via static reconciliation tests;
it does **not** import or override HCL at runtime.

## Relationship to Slice 8.12

**Slice 8.12** formalizes least-privilege writer IAM intent
(`community-data-lake-access-policy:1.0`): prefix-scoped Put/Get, delete Deny,
no ListBucket, no KMS IAM, `DenyInsecureTransport` (TLS — not at-rest).
Writer policy remains unattached; no bucket-policy Deny for missing encryption
headers was added. See [data-lake-access-control.md](./data-lake-access-control.md).

## Relationship to Slice 8.13

**Slice 8.13** formalizes the storage-abstraction port and adapter factory
(`community-data-lake-storage-policy:1.0`). The S3 adapter remains capable but
unwired; production default is the unavailable adapter. See
[data-lake-storage-abstraction.md](./data-lake-storage-abstraction.md).
Slice 8.14 (integration verification) is complete. Slice 8.15 (ingestion wiring)
is not started.

## Package symbols

```text
community-data-lake-encryption-policy:1.0
CommunityDataLakeEncryptionPolicy / default_encryption_policy()
EncryptionValidationError / validate_encryption_mode() / assert_no_kms_key_id()
EncryptionPolicyDiagnostics / diagnostics_from_encryption_policy()
```

See also: [data-lake.md](./data-lake.md),
[immutable-raw-storage.md](./immutable-raw-storage.md),
[data-lake-quarantine.md](./data-lake-quarantine.md),
[data-lake-retention.md](./data-lake-retention.md),
[data-lake-access-control.md](./data-lake-access-control.md),
`infrastructure/docs/community-data-lake.md`.

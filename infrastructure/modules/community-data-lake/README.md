# community-data-lake (Slice 8.1)

Foundation OpenTofu module for the CodeStrata Community Data Lake: a single
private, encrypted, versioned S3 bucket. This slice creates **storage
foundation only** — it does not wire the bucket into any ingestion path.

## Fail-closed: bucket exists ≠ ingestion enabled

Creating this bucket does **not** turn on Community event ingestion.
`enable_ingestion_wire` defaults to `false` and is validated (both as a
variable validation and as a module-level `check` block) to remain `false`
in this slice. No Lambda function, EventBridge rule, S3 event notification,
or other compute is attached to the bucket. A future slice must explicitly
flip this posture, with its own review, before any producer can write
through a wired path.

## Bucket strategy: single bucket, prefix isolation

Rather than one bucket per zone, this module creates **one** private bucket
and isolates zones by key prefix:

| Zone | Prefix | Purpose |
| --- | --- | --- |
| Accepted | `raw/` | Objects that passed validation |
| Quarantine | `quarantine/` | Objects that failed validation or are pending review |

Lifecycle rules, and the writer IAM policy, are scoped per prefix so the two
zones can be retained, expired, and permissioned independently without
managing multiple buckets.

## Encryption: SSE-S3 today, SSE-KMS is a future migration

Server-side encryption uses SSE-S3 (`AES256`) via
`aws_s3_bucket_server_side_encryption_configuration`. `var.encryption_mode`
is constrained to `"sse_s3"` only. `bucket_key_enabled` is **false** (S3
Bucket Keys apply to SSE-KMS, not SSE-S3). Migrating to SSE-KMS with a
customer-managed key (for per-tenant rotation and audit trails) is a
**documented future migration** — no `aws_kms_key` or other KMS resource is
created in this slice.

Defense in depth for product writers: bucket default encryption **plus**
explicit adapter `ServerSideEncryption=AES256` Put headers. This module
does **not** attach a bucket-policy Deny for missing encryption headers
(documented Slice 8.11 limitation). Platform documents the same contract as
`community-data-lake-encryption-policy:1.0`. See
`platform/docs/community-cloud-api/data-lake-encryption.md`.

This module does not claim production data is stored or that
customer-managed KMS is enabled.

## Retention defaults are review-required

| Variable | Default | Status |
| --- | --- | --- |
| `accepted_retention_days` | 365 | Provisional / review-required (Slice 8.10) |
| `quarantine_retention_days` | 90 | Provisional; must be ≤ accepted |
| `incomplete_multipart_days` | 7 | Bucket-wide abort for incomplete multipart uploads |
| `noncurrent_version_expiration_days` | 30 | Applies to both prefixes |

Lifecycle also enables **expired delete-marker cleanup** (`expire-delete-markers`)
as a separate empty-filter rule. There are **no** storage-class transitions and
**no** S3 Object Lock resources. `force_destroy` defaults to and is validated
as `false`.

Platform documents the same contract as
`community-data-lake-retention-policy:1.0` and reconciles defaults/bounds via
static tests — Platform does not override HCL at runtime. See
`platform/docs/community-cloud-api/data-lake-retention.md`.

Do not treat these defaults as final retention policy without a separate
review of legal, storage-cost, and replay requirements. This module does not
claim production data is stored or deleted.

## IAM: writer policy document only, not attached to anything

`iam.tf` defines `data.aws_iam_policy_document.writer_policy` (and a
standalone `aws_iam_policy.writer` resource built from it) describing the
least-privilege permissions a future writer would need. **Slice 8.12** uses
stable statement SIDs:

| SID | Effect | Actions | Scope |
| --- | --- | --- | --- |
| `WriteAcceptedRawObjects` | Allow | `s3:PutObject` | `raw/*` |
| `WriteQuarantineRecords` | Allow | `s3:PutObject` | `quarantine/*` |
| `VerifyAcceptedRawObjects` | Allow | `s3:GetObject` | `raw/*` |
| `VerifyQuarantineRecords` | Allow | `s3:GetObject` | `quarantine/*` |
| `DenyAcceptedObjectDeletion` | Deny | `s3:DeleteObject`, `s3:DeleteObjectVersion` | `raw/*` |
| `DenyQuarantineObjectDeletion` | Deny | `s3:DeleteObject`, `s3:DeleteObjectVersion` | `quarantine/*` |

`s3:ListBucket` is intentionally **not** granted — writers use deterministic
keys and do not need to enumerate bucket contents. There is no
`aws_iam_role`, no role/policy attachment, no `s3:ListAllMyBuckets`, no
`Resource = "*"` S3 admin grant, and no `kms:` actions anywhere in this
module.

**This module does not attach the writer policy to any Lambda, role, or
user.** Attaching it is a distinct, later, explicitly-reviewed change
(Slice 8.13+).

### Bucket policy: DenyInsecureTransport (Slice 8.12)

`bucket_policy.tf` adds `DenyInsecureTransport` when `aws:SecureTransport=false`.
This enforces TLS in transit — it is **not** at-rest encryption (see
`encryption.tf`). Public access remains blocked by
`aws_s3_bucket_public_access_block`.

Platform documents the same access contract as
`community-data-lake-access-policy:1.0`. See
`platform/docs/community-cloud-api/data-lake-access-control.md`.

### `HeadObject` is already covered — no IAM change for Slice 8.2

Slice 8.2's Platform-side S3 adapter
(`platform/.../data_lake/infrastructure/s3_store.py`) issues a `HeadObject`
call exactly once, only after a conditional `PutObject` returns
`PreconditionFailed`, to read the existing object's digest metadata and
decide `ALREADY_EXISTS` vs `CONFLICT`. `HeadObject` is authorized by the
`s3:GetObject` action (AWS treats `HeadObject` as covered by `s3:GetObject`
IAM permissions), which the `writer_policy` document above **already
grants** on both `raw/*` and `quarantine/*`. No `iam.tf` change was made or
is needed for this. The adapter itself is not attached to any Lambda role in
this slice.

### Slice 8.9 quarantine persistence — no IAM/lifecycle HCL change

Platform Slice 8.9 implements quarantine object writes under `quarantine/`
using the same `PutObject`/`GetObject` (Head) permissions and 90-day
lifecycle already defined here. No `iam.tf` or `lifecycle.tf` change was
made for 8.9. The writer policy remains **unattached**; endpoints are not
wired.

### Slice 8.10 retention / lifecycle alignment

Slice 8.10 adds the Platform retention policy contract and strengthens HCL
guards: quarantine ≤ accepted in `validation.tf`, explicit
`expire-delete-markers` lifecycle rule, and `force_destroy == false` check.
Still unwired; no claim that production data is stored or deleted.

## No website, no ACLs, no CORS

`aws_s3_bucket_public_access_block` blocks all four public-access vectors,
`aws_s3_bucket_ownership_controls` is `BucketOwnerEnforced` (disabling
ACLs), versioning is `Enabled`, and there is no website configuration or
CORS configuration. This bucket is never served directly to clients.

## Extraction-ready

This module has no dependency on the `community-cloud-api` module and no
application Python. It can be extracted alongside the rest of
`infrastructure/` into a separate private repository without modification.

## Must not reuse other buckets

This module must not reuse, and is not reused by:

- The OpenTofu/Terraform state bucket
- Any Lambda deployment artifact bucket
- The `community-cloud-api` ECR repository

## Inputs

See `variables.tf`. Key inputs: `project_name`, `environment_name`
(`production` only in this slice), `aws_region`, `accepted_retention_days`,
`quarantine_retention_days`, `incomplete_multipart_days`,
`noncurrent_version_expiration_days`, `encryption_mode` (`sse_s3` only),
`enable_ingestion_wire` (must stay `false`), `force_destroy`, `tags`.

## Outputs

Safe outputs only — no account IDs as primary identity, no secrets. See
`outputs.tf`: `bucket_name`, `bucket_arn`, `bucket_region`,
`accepted_prefix`, `quarantine_prefix`, `writer_policy_arn`,
`writer_policy_name`, `encryption_mode`, `enable_ingestion_wire`.

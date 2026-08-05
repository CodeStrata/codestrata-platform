# Community Data Lake Access Control (Slice 8.12)

Slice 8.12 formalizes the **least-privilege IAM access product-policy contract**
for the Community Data Lake. Platform defines intent; OpenTofu defines the
writer IAM policy document; static tests reconcile the two. Nothing attaches
the writer policy or enables ingestion in this slice.

## Policy token

```text
community-data-lake-access-policy:1.0
```

`CommunityDataLakeAccessPolicy` / `default_access_policy()` capture writer
allowed/forbidden actions, prefix scoping, delete posture, and unwired
foundation limitations. `writer_policy_attached` must remain `false`.

## Writer action → adapter mapping

| IAM action | S3 adapter call | Purpose |
| --- | --- | --- |
| `s3:PutObject` | `client.put_object(...)` | Immutable accepted + quarantine writes |
| `s3:GetObject` | `client.head_object(...)` | Single retry read after `PreconditionFailed` |

There is no `s3:HeadObject` IAM action — AWS authorizes `HeadObject` via
`s3:GetObject` on the object ARN. The adapter never calls `list_objects`,
`delete_object`, or bucket-admin APIs.

## Prefix scoping

| Zone | Prefix | Writer Allow |
| --- | --- | --- |
| Accepted | `raw/` | Put + Get (verify) |
| Quarantine | `quarantine/` | Put + Get (verify) |

OpenTofu statement SIDs (stable, auditable):

- `WriteAcceptedRawObjects` / `WriteQuarantineRecords` — `s3:PutObject`
- `VerifyAcceptedRawObjects` / `VerifyQuarantineRecords` — `s3:GetObject`
- `DenyAcceptedObjectDeletion` / `DenyQuarantineObjectDeletion` — explicit Deny

## Delete posture

Writers are **denied** `s3:DeleteObject` and `s3:DeleteObjectVersion` on both
prefixes. There is no Allow delete anywhere in the writer policy. Lifecycle
expiration and delete-marker cleanup are **S3 service** behavior under bucket
lifecycle rules (Slice 8.10) — not writer identity deletes.

## Explicitly forbidden for the writer

- `s3:ListBucket`, `s3:ListAllMyBuckets`, `s3:GetBucketLocation`
- Bucket admin: policy, encryption config, lifecycle config, public access block,
  versioning, ownership controls, create/delete bucket
- `s3:*` wildcard actions or `Resource = ["*"]` grants
- Any `kms:*` or `kms:` actions (SSE-S3 only; see Slice 8.11)
- ACL/object-replication/restore/select admin actions

## Transport: DenyInsecureTransport

`bucket_policy.tf` adds `DenyInsecureTransport` when `aws:SecureTransport=false`.
This enforces **TLS in transit**. It is **not** at-rest encryption (that remains
Slice 8.11 SSE-S3). Public access remains blocked by
`aws_s3_bucket_public_access_block`; the Deny uses principal `"*"` as the
standard AWS pattern and does not grant public Allow access.

## Unattached writer; Lambda unchanged

- `aws_iam_policy.writer` exists as a standalone resource — **not attached** to
  any role, user, or Lambda.
- `enable_ingestion_wire = false` in production and module validation.
- `community-cloud-api` Lambda IAM retains **logs + ECR pull only** — no S3,
  no Data Lake env vars, no writer attachment.

## Future analytics and quarantine separation

`analytics_quarantine_separated` is `true` on the Platform policy. **Future
analytics reader roles must not automatically include `quarantine/*` read
access.** No analytics IAM exists in this slice.

A future **quarantine reader** role (human review / incident response) requires
a separate, explicitly reviewed approval path — it must not be folded into a
generic analytics reader.

## Fail-closed posture

- No `app.py` / `deployment/wiring.py` / endpoint imports of access policy or
  data lake storage.
- Engine remains unaware of the data lake.
- Platform references infrastructure via static reconciliation tests only — it
  does **not** import or override HCL at runtime.
- **Slice 8.13** (storage abstraction / projected-object port) is **not started**
  for wiring — see [data-lake-storage-abstraction.md](./data-lake-storage-abstraction.md).
- **Slice 8.14** (integration verification) is **complete** — see
  `platform/verification/community_data_lake/`.
- **Slice 8.15** (ingestion wiring / writer attachment) is **not started**.

## Relationship to retention and encryption

| Slice | Concern |
| --- | --- |
| 8.10 | Lifecycle expiration, delete-marker cleanup — S3 service, not writer delete |
| 8.11 | SSE-S3 at rest — bucket default + explicit Put headers; no KMS IAM |
| 8.12 | Least-privilege writer IAM intent, prefix scoping, delete Deny, TLS Deny |

Access control complements encryption and retention: writers can Put/Get for
retry classification but cannot delete, list, administer the bucket, or use KMS
keys under the current SSE-S3 foundation.

## Package symbols

```text
community-data-lake-access-policy:1.0
CommunityDataLakeAccessPolicy / default_access_policy()
AccessValidationError / validate_access_action_sets()
AccessPolicyDiagnostics / diagnostics_from_access_policy()
```

See also: [data-lake.md](./data-lake.md),
[immutable-raw-storage.md](./immutable-raw-storage.md),
[data-lake-quarantine.md](./data-lake-quarantine.md),
[data-lake-retention.md](./data-lake-retention.md),
[data-lake-encryption.md](./data-lake-encryption.md),
`infrastructure/docs/community-data-lake.md`,
`infrastructure/modules/community-data-lake/README.md`.

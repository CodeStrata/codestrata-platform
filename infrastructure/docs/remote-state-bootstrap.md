# OpenTofu remote-state bootstrap (Slice 17.2)

**Policy:** `community-cloud-remote-state-policy:1.0`  
**Register:** `community-cloud-remote-state-register:1.0`  
**Region:** `us-west-2`  
**Profile (operator):** `codestrata_infra`

## Architecture

```text
OpenTofu
    ↓
Dedicated private S3 state bucket
    ├── production state object
    ├── native S3 lockfile (use_lockfile = true)
    ├── versioning enabled
    ├── SSE-S3 encryption
    └── Block Public Access (all four flags)
```

**No DynamoDB.** Completely separate from the Community Data Lake bucket.

## Bootstrap (operator)

```bash
export AWS_PROFILE=codestrata_infra
export AWS_REGION=us-west-2
./infrastructure/scripts/bootstrap-remote-state.sh
```

Creates **only** the remote-state S3 bucket, writes gitignored `infrastructure/production/backend.hcl`,
and runs `tofu init` for `infrastructure/production/` against the S3 backend.

**Bootstrap method:** AWS CLI ensures the bucket + required controls (operator IAM cannot
refresh `aws_s3_bucket` without `s3:GetBucketPolicy` / `GetBucketTagging` /
`GetBucketWebsite`). OpenTofu local state then manages the four control resources
(versioning, SSE-S3, public access block, ownership) for idempotent drift detection.

Does **not** run production `tofu apply`.

## Recovery (state object)

1. List state object versions in the dedicated bucket (requires `s3:ListBucketVersions`)  
2. Select a known-good prior version  
3. Restore/copy under owner control  
4. `tofu init`  
5. `tofu plan`  
6. Inspect drift before any apply  

Never casually edit the state file. Restored state must always be followed by init + plan + owner review.

## Stale lock recovery

1. Confirm no active OpenTofu operation is running  
2. Use `tofu force-unlock <LOCK_ID>` only after that confirmation  
3. Do not casually delete native lock objects from S3  

Do not force-unlock production state for routine testing.

## IAM notes

**Operator bootstrap (Slice 17.2)** requires at least:

- `s3:CreateBucket`, `s3:ListBucket`, `s3:PutBucketVersioning`, `s3:GetBucketVersioning`
- `s3:PutEncryptionConfiguration`, `s3:GetEncryptionConfiguration`
- `s3:PutBucketPublicAccessBlock`, `s3:GetBucketPublicAccessBlock`
- `s3:PutBucketOwnershipControls`, `s3:GetBucketOwnershipControls`
- `s3:GetObject` / `s3:PutObject` / `s3:DeleteObject` (backend + native lockfile)

Optional for full `aws_s3_bucket` resource refresh (not required for this hybrid bootstrap):

- `s3:GetBucketPolicy`, `s3:GetBucketTagging`, `s3:GetBucketWebsite`

## Future IAM (Slice 17.3 OIDC role)

- `s3:ListBucket` on the state bucket (as required)  
- `s3:GetObject` / `s3:PutObject` on the state object  
- `s3:GetObject` / `s3:PutObject` / `s3:DeleteObject` on the lockfile  
- **No** DynamoDB actions  

## Slice boundary

| Slice | Owns |
| ----- | ---- |
| 17.2 | This bootstrap only |
| 17.3 | GitHub OIDC deployment role |

`start_slice_17_3 = false` during 17.2.

## Related

- GitHub OIDC identity (Slice 17.3): `infrastructure/docs/github-aws-oidc.md`

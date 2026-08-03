# Future Community Data Lake (deferred)

Slice 7.14 does **not** create data-lake resources.

Community Data Lake resources are intentionally deferred. Future S3 buckets,
lifecycle, partitioning, encryption, access, and ingestion notifications will be
added through a separate `infrastructure/modules/data-lake` module.

## Planned location (not created yet)

```text
infrastructure/modules/data-lake/
```

Future environment roots (`dev/`, `staging/`, `production/`) may compose that
module independently of `community-cloud-api`.

## Potential future concerns (undecided)

- Raw / accepted / quarantine zones
- Partitioning strategy
- Object identity and deduplication
- Encryption and KMS
- Lifecycle and retention
- Schema registry
- Access control
- Ingestion notifications
- Replay and deletion
- Privacy review

## Must not reuse

- OpenTofu/Terraform state bucket
- Lambda deployment artifact bucket
- ECR repository

as the Community Data Lake.

Do not decide these prematurely in Slice 7.14.

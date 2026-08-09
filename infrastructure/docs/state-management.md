# State management

## Policy

Do not commit:

- `terraform.tfstate` / backups
- `.terraform/`
- generated plans
- live `backend.tf` with account-specific values
- credential files

See `infrastructure/.gitignore`.

## Example backend

`production/backend.tf.example` documents a remote S3 backend with:

- Encryption (`encrypt = true`)
- Native S3 lockfile locking (`use_lockfile = true`) — **no DynamoDB**
- Restricted IAM for state objects and lockfile
- Bucket versioning
- Block Public Access (required at bootstrap)
- Separate state key per environment

Copy to `backend.tf` locally and fill placeholders. Do not commit live values.

Authoritative CI/CD architecture:
[`platform/docs/deployment/community-cloud-cicd-architecture.md`](../../platform/docs/deployment/community-cloud-cicd-architecture.md).

## Bootstrap

Slice **17.2** creates the dedicated state bucket (versioning, encryption,
public-access block, native lockfile configuration). This documentation does
**not** create AWS resources. Bootstrap must **not** create DynamoDB.

## Separation rules

| Store | Role |
| --- | --- |
| OpenTofu state bucket | Infrastructure state + native lockfile only |
| ECR repository | Container images only |
| Community Data Lake bucket | Community telemetry events only (product path) |

Never reuse the state bucket, ECR repository, or a Lambda deployment artifact
bucket as the Community Data Lake.

## Environments

Production uses its own state. Future `dev/` / `staging/` roots (if ever added)
must each have separate state — do not use one multi-environment state file.
v0.2.0 environment strategy remains **production only**.

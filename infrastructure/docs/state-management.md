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

- Encryption
- Locking (e.g. DynamoDB)
- Restricted IAM
- Bucket versioning
- Separate state key per environment

Copy to `backend.tf` locally and fill placeholders. Do not commit live values.

## Bootstrap

This slice does **not** create the state bucket automatically. Bootstrap state
storage through a reviewed process outside the Community Cloud module.

## Separation rules

| Store | Role |
| --- | --- |
| OpenTofu state bucket | Infrastructure state only |
| ECR repository | Container images only |
| Future data-lake buckets | Community events only (not yet created) |

Never reuse the state bucket, ECR repository, or a Lambda deployment artifact
bucket as the Community Data Lake.

## Environments

Production uses its own state. Future `dev/` and `staging/` roots must each
have separate state — do not use one multi-environment state file.

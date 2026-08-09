# Slice 17.6 — Runtime security (Secrets, IAM, permissions)

Prepares production Insights auth + Community Data Lake runtime IAM **without**
enabling ingestion.

## Architecture

| Concern | Authority |
|---------|-----------|
| Secret **identifiers** | Slice 15.9 + Lambda env (names only) |
| Secret **values** | AWS Secrets Manager via `configure-production-secrets.sh` (never Git/IaC/state/reports) |
| Insights S3 read | `codestrata-community-insights-production-reader` (`production/runtime-security.tf`) |
| Insights secret read | `codestrata-community-insights-production-secrets` |
| Data Lake writer | Exists unattached — **deferred to Slice 17.7** |
| Ingestion flag | `CODESTRATA_INGESTION_ENABLED=false` |

## Operator attach (required once)

See `infrastructure/bootstrap/github-oidc/OWNER_ATTACH_RUNTIME_SECURITY.md`.

## Scripts

```bash
export AWS_PROFILE=codestrata_infra AWS_REGION=us-west-2
./infrastructure/scripts/configure-production-secrets.sh generate
./infrastructure/scripts/configure-production-runtime-iam.sh
# Prefer OpenTofu apply of production/runtime-security.tf for IAM drift control
```

## Image update

Rebuild Lambda image after `AwsSecretsPort` + `platform[lambda]` boto3:

`IMAGE_TAG=v0.2.0-foundation-sv17-6 ./infrastructure/scripts/apply-production-staged.sh stage-b`

Then point `lambda_image_uri` at the new immutable tag/digest and apply.

## Rotation

See `infrastructure/docs/runtime-security-secret-rotation.md`.

## Verification

```bash
PYTHONPATH=. .venv/bin/python -m verification.community_cloud_runtime_security
```

Report: `reports/verification/sv17-6/community-cloud-runtime-security-verification.json`

## Explicit non-goals

- Slice 17.7 / writer attach / ingestion ON
- Insights frontend / Docs
- Bedrock / OpenAI / OpenRouter credentials
- Commit / tag / publish

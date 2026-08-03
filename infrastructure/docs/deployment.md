# Deployment

## Prerequisites

- OpenTofu `>= 1.6` (`tofu`)
- AWS credentials configured for the target account (plan/apply only)
- Docker (image build)
- Python 3.12+ (local tests / validate script)

Operational command path:

```bash
tofu init
tofu fmt
tofu validate
tofu plan
tofu apply   # human-approved only; no auto-approve script in this slice
```

## Packaging

Image bootstrap order (first deployment):

1. Prefer creating the ECR repository first (targeted apply) or using an
   existing registry URI, then push an immutable tag, then set
   `lambda_image_uri` and apply the full stack.
2. Do not push during `tofu plan`.

Build locally (no push):

```bash
./infrastructure/scripts/build-community-cloud-api.sh --tag v0.2.0-foundation
```

Push to the private ECR repository with an **explicit** registry and
immutable tag/digest (separate operator step — not automated here).

Set `lambda_image_uri` in a local (gitignored) `terraform.tfvars`.

Plan:

```bash
./infrastructure/scripts/plan-production.sh --var-file /path/to/terraform.tfvars
```

Apply only with explicit human approval (no auto-approve helper).

## Runtime configuration

Lambda environment (non-secret):

| Variable | Foundation value |
| --- | --- |
| `CODESTRATA_DEPLOYMENT_MODE` | `production_foundation` |
| `CODESTRATA_COMMUNITY_API_VERSION` | `1.0` |
| `CODESTRATA_AUTHENTICATION_ENABLED` | `true` |
| `CODESTRATA_RATE_LIMIT_ENABLED` | `true` |
| `CODESTRATA_INGESTION_ENABLED` | `false` |
| `CODESTRATA_AUTHENTICATION_MODE` | `enabled_verifier_unavailable` |
| `CODESTRATA_RATE_LIMIT_MODE` | `api_gateway_plus_process_local` |

## Health smoke

After a deployment exists:

```bash
./infrastructure/scripts/smoke-health.sh "https://{api-id}.execute-api.{region}.amazonaws.com"
```

Calls only `/api/v1/health`. Never run against production automatically from CI
in this slice.

## Local validation (no cloud)

```bash
./infrastructure/scripts/validate.sh
```

## Image identity

Prefer immutable release tags or digests. Do not use floating `latest` as the
only deployment identity. ECR repository tag mutability is `IMMUTABLE`.

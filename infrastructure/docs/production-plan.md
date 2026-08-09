# Slice 17.4 — Production OpenTofu plan

**Status:** Plan-only. Product apply is **not** started (Slice 17.5 deferred).  
**Policy:** `community-cloud-production-plan-policy:1.0`  
**Register:** `community-cloud-production-plan-register:1.0`  
**Verification:** `verification/community_cloud_production_plan`

## What the plan creates

First authoritative production plan for Community Cloud in **us-west-2** / **production**.

Root modules wired today:

- `module.community_cloud_api` — HTTP API Gateway v2, Lambda (image/arm64/512MB/30s), ECR (`codestrata/community-cloud-api`, private, IMMUTABLE, scan on push), CloudWatch log group, Lambda execution IAM (logging + ECR pull only)
- `module.community_data_lake` — private Data Lake bucket `codestrata-community-data-lake-production` (distinct from state bucket pattern `codestrata-opentofu-state-production-*`), encryption/PAB/versioning/lifecycle, **unattached** writer IAM policy

Deferred / not in production root:

- `community-insights-auth` (not wired)
- Secrets Manager application secrets
- DynamoDB / Athena / Glue / RDS / Redis / NAT / EC2 / ECS / EKS
- Production ingestion (`enable_ingestion=false`, `enable_ingestion_wire=false`)

Plan summary (authoritative): **add=21, change=0, destroy=0, replace=0**.

## Ingestion remains off

Production ingestion stays hard-gated off in OpenTofu. Slice 17.5 may apply infrastructure; ingestion activation remains a later slice.

## How to run a local plan

```bash
export AWS_PROFILE=codestrata_infra
export AWS_REGION=us-west-2
# Ensure infrastructure/production/backend.hcl exists (gitignored) from remote-state bootstrap.
./infrastructure/scripts/plan-production.sh
# Optional binary plan output (gitignored under .local/):
./infrastructure/scripts/plan-production.sh --out .local/sv17-4.tfplan
```

The script **never applies** and never auto-approves.

## GitHub workflow

[`.github/workflows/infrastructure-plan.yml`](../../.github/workflows/infrastructure-plan.yml):

- Offline job: fmt / init `-backend=false` / validate
- Authenticated plan job: OIDC + remote backend + `tofu plan` (no apply)
- Structural until owner push activates live OIDC plan

## Limitations (accepted for 17.4)

- First authoritative plan executed locally under `codestrata_infra`
- Live GitHub plan workflow awaits commit/push
- `lambda_image_uri` may use a plan placeholder (image push deferred)
- Apply-permission register proposed for 17.5 but **not attached**
- Worktree may be uncommitted

## Slice 17.5

Foundation apply is started in Slice 17.5 (`verification/community_cloud_infrastructure_deployment`).
This plan package remains plan-only. Slice 17.6 is complete; Slice 17.7 is **not** started.

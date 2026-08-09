# Slice 17.5 — Infrastructure deployment (foundation apply)

**Status:** Foundation deploy for Community Cloud production. Ingestion stays **OFF**.  
**Policy:** `community-cloud-infrastructure-deployment-policy:1.0`  
**Register:** `community-cloud-production-deployment-register:1.0`  
**Verification:** `verification/community_cloud_infrastructure_deployment`

## What this slice deploys

Staged OpenTofu apply of the Slice 17.4 plan (add=21) in **us-west-2** / **production**:

| Stage | Scope |
|-------|--------|
| A | ECR repository + lifecycle, Data Lake bucket + encryption/PAB/versioning, runtime IAM roles/policies, CloudWatch log group |
| B | Build/push `codestrata/community-cloud-api` **arm64** image (`CODESTRATA_INGESTION_ENABLED=false` in Dockerfile) |
| C | Lambda (image package) + HTTP API Gateway v2 |
| D | Post-apply plan must show **zero drift** |

## Hard non-actions

- Production ingestion remains off (`enable_ingestion=false`, `enable_ingestion_wire=false`)
- Data Lake **writer IAM policy stays unattached**
- No Secrets Manager application secrets
- No Insights / Docs deploy
- No DynamoDB / Athena / Glue / RDS / Redis
- **Slice 17.6 complete; Slice 17.7 not started**

## Staged local apply

```bash
export AWS_PROFILE=codestrata_infra
export AWS_REGION=us-west-2
# Requires operator IAM attach (see OWNER_ATTACH_PRODUCTION_APPLY.md) when blocked.
./infrastructure/scripts/apply-production-staged.sh          # all stages
./infrastructure/scripts/apply-production-staged.sh stage-a  # foundation only
```

The script applies **saved plan files** after gates; it does not enable ingestion.

## GitHub apply policy

- IAM contract: `infrastructure/bootstrap/github-oidc/codestrata-github-infrastructure-apply-policy.json`
- Metadata wrapper: `platform/policies/codestrata_github_infrastructure_apply_policy.json`
- Attach helper: `infrastructure/scripts/attach-github-infrastructure-apply-policy.sh`
- Operator attach doc: `infrastructure/bootstrap/github-oidc/OWNER_ATTACH_PRODUCTION_APPLY.md`
- Operator policy: `infrastructure/bootstrap/github-oidc/operator-iam-production-apply-policy.json`

## GitHub workflow

[`.github/workflows/infrastructure-apply.yml`](../../.github/workflows/infrastructure-apply.yml):

- `workflow_dispatch` **only** (never `pull_request`)
- `environment: production` + OIDC `configure-aws-credentials`
- Requires confirmation input `APPLY-PRODUCTION`
- Regenerates or requires a reviewed plan; **fails closed** on destroy/replace
- Applies the **saved plan file** (no casual `-auto-approve` on an unreviewed plan)
- Post-apply plan zero-drift check
- Live run awaits push + attached apply IAM

## Rollback posture

Documented rollback (no auto-destroy):

1. Remove Lambda + API Gateway first (retain ECR image tags / Data Lake objects as needed)
2. Keep Data Lake bucket unless explicitly retiring storage
3. Never attach the writer policy during rollback
4. Never flip ingestion on while rolling back
5. Re-plan with destroy/replace gates before any reverse apply

`rollback_ready=true` means this posture is documented and scripts/gates preserve it—not that destroy has been executed.

## Limitations (accepted for 17.5)

- Apply may run locally under `codestrata_infra` (GitHub apply structural until push + IAM)
- Operator IAM attach may block AWS mutation until owner completes attach
- Image push is part of the staged path (Stage B) after ECR exists
- Worktree may be uncommitted

## Slice 17.6

**Complete** (`verification/community_cloud_runtime_security`). Runtime secrets identifiers +
operational values in Secrets Manager only. Ingestion remains off. Writer remains unattached
(deferred to Slice 17.7).

## Slice 17.7

**Not started.** No writer attachment, no ingestion enablement.

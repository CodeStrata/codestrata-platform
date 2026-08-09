# Slice 17.5 — Operator IAM attach (required once)

`codestrata_infra` can plan against remote state but cannot create Lambda/ECR/API/IAM
product resources until this managed policy is attached.

## Attach (owner / IAM admin)

Policy document (repo):

`infrastructure/bootstrap/github-oidc/operator-iam-production-apply-policy.json`

Attach to IAM user `codestrata_infra` (Console or CLI with IAM admin):

```bash
# Example (run as IAM admin — not as codestrata_infra if CreatePolicy is denied):
aws iam create-policy \
  --policy-name CodeStrataOperatorProductionApply \
  --policy-document file://infrastructure/bootstrap/github-oidc/operator-iam-production-apply-policy.json

aws iam attach-user-policy \
  --user-name codestrata_infra \
  --policy-arn arn:aws:iam::<ACCOUNT>:policy/CodeStrataOperatorProductionApply
```

Also refresh the OIDC bootstrap policy so GitHub apply policy creation is allowed
(repo already lists `CodeStrataGitHubInfrastructureApply`):

`infrastructure/bootstrap/github-oidc/operator-iam-bootstrap-policy.json`

## After attach

```bash
export AWS_PROFILE=codestrata_infra AWS_REGION=us-west-2
./infrastructure/scripts/attach-github-infrastructure-apply-policy.sh
./infrastructure/scripts/apply-production-staged.sh all
```

## Scope

- Data Lake bucket `codestrata-community-data-lake-production` only (not state bucket mutation beyond existing state access)
- ECR `codestrata/community-cloud-api` + image push
- Lambda `codestrata-community-cloud-production-api`
- API Gateway v2
- Runtime IAM role + unattached writer policy
- CloudWatch log group
- Create/attach `CodeStrataGitHubInfrastructureApply` on GitHub role

No AdministratorAccess. No Secrets Manager app secrets. No ingestion enablement.

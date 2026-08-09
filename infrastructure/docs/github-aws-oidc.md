# GitHub Actions → AWS OIDC (Slice 17.3)

**Policy:** `community-cloud-github-oidc-policy:1.0`  
**Register:** `codestrata-github-aws-identity-register:1.0`  
**Region:** `us-west-2`  
**Repository:** `CodeStrata/codestrata-platform`

## Why OIDC

GitHub Actions obtains short-lived AWS credentials via OpenID Connect.
Long-lived `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` values must **not** be
stored in GitHub secrets for CodeStrata CI/CD.

```text
GitHub Actions
    ↓  OIDC token (aud=sts.amazonaws.com)
AWS IAM OIDC provider (token.actions.githubusercontent.com)
    ↓  AssumeRoleWithWebIdentity
codestrata-github-actions-production
    ↓  short-lived STS session (≤ 1h)
OpenTofu / deployment workflows
```

## Trust

Exact subject (no org-wide wildcards, no forks):

`repo:CodeStrata/codestrata-platform:environment:production`

Audience: `sts.amazonaws.com`

## Role vs local operator

| Identity | Purpose |
| -------- | ------- |
| `codestrata_infra` (IAM user) | Local bootstrap / emergency / Bedrock testing |
| `codestrata-github-actions-production` | GitHub CI/CD only via OIDC |

Normal CI/CD must not use the local user's access keys.

## Permissions progression

| Slice | Capability |
| ----- | ---------- |
| 17.3 | OIDC + `CodeStrataGitHubRemoteStateAccess` (dedicated state bucket only) |
| 17.4 | `CodeStrataGitHubInfrastructurePlan` contract defined (read-only plan); attach optional; first authoritative plan may run locally under `codestrata_infra` |
| 17.5+ | Narrow apply/deploy permissions from real plan |

**No** AdministratorAccess, PowerUserAccess, IAMFullAccess, DynamoDB,
application Secrets, Data Lake analytics, or Bedrock InvokeModel on this role
for plan. Product mutation remains Slice 17.5.

## Bootstrap

```bash
export AWS_PROFILE=codestrata_infra
export AWS_REGION=us-west-2
./infrastructure/scripts/bootstrap-github-oidc.sh
```

### Operator IAM prerequisite

`codestrata_infra` must be able to manage the GitHub OIDC provider and the
`codestrata-github-actions-production` role. Attach the policy document:

`infrastructure/bootstrap/github-oidc/operator-iam-bootstrap-policy.json`

(via Console/root or an IAM admin). Re-run the bootstrap script after attach.

## GitHub production environment

Create/protect GitHub Environment **`production`**:

- Deployment branch/ref protection as desired
- Required reviewers when available
- **No** AWS access-key secrets
- Cloudflare credentials remain a separate frontend concern (not AWS OIDC)

## Workflow

Structural identity workflow (live execution requires owner push):

`.github/workflows/aws-identity-check.yml`

- `permissions.id-token: write` + `contents: read`
- `environment: production`
- Assumes the GitHub role via `aws-actions/configure-aws-credentials`
- Safe checks only (`sts get-caller-identity`, state bucket head)
- **Never** runs `tofu apply`

Ordinary `ci.yml` must **not** gain `id-token: write`.

## Credential incident procedure

1. Disable/rotate any leaked long-lived keys immediately  
2. Confirm GitHub secrets do not store AWS access keys  
3. Review OIDC trust subject / audience  
4. Re-run identity-check workflow after remediation  

## Boundaries

- Cloudflare ≠ AWS OIDC  
- Application Secrets Manager values → Slice 17.6  
- Production OpenTofu plan → Slice 17.4  
- Product apply/deploy → later slices  

## Related

- Architecture: `platform/docs/deployment/community-cloud-cicd-architecture.md`  
- Remote state: `infrastructure/docs/remote-state-bootstrap.md`

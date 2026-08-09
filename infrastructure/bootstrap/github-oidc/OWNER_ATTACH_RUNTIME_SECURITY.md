# Slice 17.6 — Operator IAM attach (required once)

`codestrata_infra` cannot create Insights secrets or create/attach runtime managed
policies until this managed policy is attached.

**Only one local AWS profile is typically present (`codestrata_infra`).** An IAM
admin principal (Console root/IAM admin, or a separate admin profile) must run
the attach step. `codestrata_infra` must not grant itself permissions.

## Attach (owner / IAM admin)

Policy document (repo):

`infrastructure/bootstrap/github-oidc/operator-iam-runtime-security-policy.json`

Preferred (idempotent create-or-update + attach):

```bash
# IAM admin profile — NOT codestrata_infra if CreatePolicy is denied
export AWS_PROFILE=<iam-admin-profile> AWS_REGION=us-west-2
./infrastructure/scripts/attach-operator-runtime-security.sh
```

Manual equivalent:

```bash
aws iam create-policy \
  --policy-name CodeStrataOperatorRuntimeSecurity \
  --policy-document file://infrastructure/bootstrap/github-oidc/operator-iam-runtime-security-policy.json
# If the policy already exists, create a new default version from the same JSON instead.

aws iam attach-user-policy \
  --user-name codestrata_infra \
  --policy-arn arn:aws:iam::<ACCOUNT>:policy/CodeStrataOperatorRuntimeSecurity
```

## After attach (as codestrata_infra)

```bash
export AWS_PROFILE=codestrata_infra AWS_REGION=us-west-2

./infrastructure/scripts/configure-production-secrets.sh generate
./infrastructure/scripts/configure-production-runtime-iam.sh

# Optional drift control: tofu apply infrastructure/production (includes runtime-security.tf)
# Rebuild image with AwsSecretsPort:
IMAGE_TAG=v0.2.0-foundation-sv17-6 ./infrastructure/scripts/apply-production-staged.sh stage-b

./infrastructure/scripts/attach-github-infrastructure-apply-policy.sh
```

## Scope

- Exact Insights secrets: `codestrata/insights/dashboard-password`, `codestrata/insights/session-secret`
- Managed policies: `codestrata-community-insights-production-reader`, `codestrata-community-insights-production-secrets`
- Attach those policies to `codestrata-community-cloud-production-lambda`
- Lambda env identifier updates only (no secret values)
- IAM SimulatePrincipalPolicy for readiness checks
- Data Lake list/get for no-new-event gate
- GitHub InfrastructureApply attach

## Explicitly out of scope

- Attaching `codestrata-community-data-lake-production-writer` (Slice 17.7)
- Enabling `CODESTRATA_INGESTION_ENABLED`
- AdministratorAccess / PowerUserAccess
- Bedrock / OpenAI / OpenRouter secrets
- Secrets Manager `ListSecrets` / `*` resource wildcards beyond create-by-name condition

# Community Insights Auth (Slice 15.9)

Infrastructure **contracts** for future deployment of shared-password Insights auth.

## In scope (source only)

- Secrets Manager **identifiers**:
  - `codestrata/insights/dashboard-password`
  - `codestrata/insights/session-secret`
- Least-privilege `secretsmanager:GetSecretValue` for auth runtime only
- Explicit `enable_module = false` (no deploy in 15.9)

## Out of scope

- Creating real secrets
- Calling AWS
- Deploying Lambda/API/DNS
- Frontend IAM (must remain empty for Secrets Manager)
- Cognito / OAuth / MFA

## IAM notes

Auth runtime: `GetSecretValue` on the two secret ARNs only.

Data Lake reader role (if separate) must **not** gain Secrets Manager access for
dashboard password. Insights SPA has **zero** Secrets Manager permissions.

Do not grant S3 Put/Delete to the auth role.

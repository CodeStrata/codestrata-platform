# Slice 17.7 — Operator IAM attach for production ingestion (required once)

`codestrata_infra` cannot create the Community client-credentials secret or the
managed ingestion-secrets policy until this operator policy is attached.

**Live progress (as of Slice 17.7 activation):**

- Data Lake writer already attached to production Lambda role
- `CODESTRATA_INGESTION_ENABLED=true` and wire flags live
- Health 200; unauthenticated ingestion returns 401
- Credential verifier fail-closed (503) until fingerprints secret exists
- **Still blocked:** `CreateSecret` / `DescribeSecret` for
  `codestrata/community/client-credentials`

**Only one local AWS profile is typically present (`codestrata_infra`).** An IAM
admin principal (Console root/IAM admin, or a separate admin profile) must run
the attach step. `codestrata_infra` must not grant itself permissions.

## Attach (owner / IAM admin)

Policy document (repo):

`infrastructure/bootstrap/github-oidc/operator-iam-production-ingestion-policy.json`

```bash
# IAM admin profile — NOT codestrata_infra if CreatePolicy is denied
export AWS_PROFILE=<iam-admin-profile> AWS_REGION=us-west-2
./infrastructure/scripts/attach-operator-production-ingestion.sh
```

Or manually:

```bash
export AWS_PROFILE=<iam-admin-profile> AWS_REGION=us-west-2

POLICY_NAME=CodeStrataOperatorProductionIngestion
POLICY_FILE=infrastructure/bootstrap/github-oidc/operator-iam-production-ingestion-policy.json

ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
POLICY_ARN="arn:aws:iam::${ACCOUNT}:policy/${POLICY_NAME}"

if aws iam get-policy --policy-arn "${POLICY_ARN}" >/dev/null 2>&1; then
  aws iam create-policy-version \
    --policy-arn "${POLICY_ARN}" \
    --policy-document "file://${POLICY_FILE}" \
    --set-as-default
else
  aws iam create-policy \
    --policy-name "${POLICY_NAME}" \
    --policy-document "file://${POLICY_FILE}"
fi

aws iam attach-user-policy \
  --user-name codestrata_infra \
  --policy-arn "${POLICY_ARN}"
```

## After attach (as codestrata_infra)

```bash
export AWS_PROFILE=codestrata_infra AWS_REGION=us-west-2

# 1) Generate Community client credential (prints token ONCE; evidence is fingerprint-only)
./infrastructure/scripts/configure-production-ingestion-credentials.sh

# 2) Re-assert writer + ingestion env (idempotent; writer already attached)
./infrastructure/scripts/activate-production-ingestion.sh

# 3) Run synthetic five-stream + quarantine validation, then:
PYTHONPATH=. python -m verification.community_cloud_production_ingestion
```

## Scope

- Attach/detach `codestrata-community-data-lake-production-writer` on
  `codestrata-community-cloud-production-lambda`
- Secrets Manager create/put/get for `codestrata/community/client-credentials-*`
- Create/manage `codestrata-community-ingestion-production-secrets` (GetSecretValue for Lambda)
- Lambda `UpdateFunctionConfiguration` for production API function
- S3 ListBucket/GetObject on the production Data Lake for validation
- IAM `SimulatePrincipalPolicy` for readiness checks

## Explicitly out of scope

- AdministratorAccess / PowerUserAccess
- `s3:DeleteObject` on the Data Lake (beyond existing production-apply if present)
- Detaching Insights reader/secrets policies
- Hardcoding tokens in Git, OpenTofu, or evidence files
- Enabling ingestion before writer attachment verification

#!/usr/bin/env bash
# Slice 17.7 — Owner/IAM-admin attach of CodeStrataOperatorProductionIngestion.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
POLICY_DOC="${ROOT}/infrastructure/bootstrap/github-oidc/operator-iam-production-ingestion-policy.json"
POLICY_NAME="CodeStrataOperatorProductionIngestion"
USER_NAME="${OPERATOR_USER:-codestrata_infra}"

export AWS_PROFILE="${AWS_PROFILE:?AWS_PROFILE is required (IAM admin)}"
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_DEFAULT_REGION="${AWS_REGION}"

ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
POLICY_ARN="arn:aws:iam::${ACCOUNT}:policy/${POLICY_NAME}"

echo "==> ensure ${POLICY_NAME}"
if aws iam get-policy --policy-arn "${POLICY_ARN}" >/dev/null 2>&1; then
  VERSIONS="$(aws iam list-policy-versions --policy-arn "${POLICY_ARN}" --query 'Versions[?IsDefaultVersion==`false`].VersionId' --output text)"
  COUNT="$(echo "${VERSIONS}" | wc -w | tr -d ' ')"
  if [[ "${COUNT}" -ge 4 ]]; then
    OLDEST="$(aws iam list-policy-versions --policy-arn "${POLICY_ARN}" --query 'Versions[?IsDefaultVersion==`false`]|sort_by(@,&CreateDate)[0].VersionId' --output text)"
    aws iam delete-policy-version --policy-arn "${POLICY_ARN}" --version-id "${OLDEST}"
  fi
  aws iam create-policy-version --policy-arn "${POLICY_ARN}" --policy-document "file://${POLICY_DOC}" --set-as-default >/dev/null
else
  aws iam create-policy --policy-name "${POLICY_NAME}" --policy-document "file://${POLICY_DOC}" \
    --description "CodeStrata operator Slice 17.7 production ingestion (writer attach + community credentials). No AdministratorAccess." >/dev/null
fi
aws iam attach-user-policy --user-name "${USER_NAME}" --policy-arn "${POLICY_ARN}"
echo "attach-operator-production-ingestion=ok"
echo "Next (codestrata_infra): ./infrastructure/scripts/configure-production-ingestion-credentials.sh && ./infrastructure/scripts/activate-production-ingestion.sh"

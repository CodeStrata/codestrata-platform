#!/usr/bin/env bash
# Slice 17.5 — Create/attach CodeStrataGitHubInfrastructureApply (no product apply).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
POLICY_DOC="${ROOT}/infrastructure/bootstrap/github-oidc/codestrata-github-infrastructure-apply-policy.json"
POLICY_NAME="CodeStrataGitHubInfrastructureApply"
ROLE_NAME="codestrata-github-actions-production"

export AWS_PROFILE="${AWS_PROFILE:-codestrata_infra}"
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_DEFAULT_REGION="${AWS_REGION}"

ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
POLICY_ARN="arn:aws:iam::${ACCOUNT}:policy/${POLICY_NAME}"

echo "==> ensure managed policy ${POLICY_NAME}"
if aws iam get-policy --policy-arn "${POLICY_ARN}" >/dev/null 2>&1; then
  echo "policy exists; creating new default version"
  # Keep at most 4 non-default versions; delete oldest if needed.
  VERSIONS="$(aws iam list-policy-versions --policy-arn "${POLICY_ARN}" --query 'Versions[?IsDefaultVersion==`false`].VersionId' --output text)"
  COUNT="$(echo "${VERSIONS}" | wc -w | tr -d ' ')"
  if [[ "${COUNT}" -ge 4 ]]; then
    OLDEST="$(aws iam list-policy-versions --policy-arn "${POLICY_ARN}" --query 'Versions[?IsDefaultVersion==`false`]|sort_by(@,&CreateDate)[0].VersionId' --output text)"
    aws iam delete-policy-version --policy-arn "${POLICY_ARN}" --version-id "${OLDEST}"
  fi
  aws iam create-policy-version \
    --policy-arn "${POLICY_ARN}" \
    --policy-document "file://${POLICY_DOC}" \
    --set-as-default >/dev/null
else
  aws iam create-policy \
    --policy-name "${POLICY_NAME}" \
    --policy-document "file://${POLICY_DOC}" \
    --description "CodeStrata GitHub OIDC production infrastructure apply (Slice 17.5). Narrow mutation for reviewed 21-resource plan. No AdministratorAccess." \
    >/dev/null
fi

echo "==> attach to ${ROLE_NAME}"
aws iam attach-role-policy --role-name "${ROLE_NAME}" --policy-arn "${POLICY_ARN}"

echo "==> attached policies (names only)"
aws iam list-attached-role-policies --role-name "${ROLE_NAME}" \
  --query 'AttachedPolicies[].PolicyName' --output text

echo "NOTE: This script does not run tofu apply."

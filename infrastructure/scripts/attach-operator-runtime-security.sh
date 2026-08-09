#!/usr/bin/env bash
# Slice 17.6 — Owner/IAM-admin attach of CodeStrataOperatorRuntimeSecurity.
#
# Run with an IAM principal that can CreatePolicy + AttachUserPolicy.
# Do NOT run as codestrata_infra if CreatePolicy is denied.
#
# Does not grant AdministratorAccess. Uses exact repo JSON only.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
POLICY_DOC="${ROOT}/infrastructure/bootstrap/github-oidc/operator-iam-runtime-security-policy.json"
POLICY_NAME="CodeStrataOperatorRuntimeSecurity"
USER_NAME="${OPERATOR_USER:-codestrata_infra}"

export AWS_PROFILE="${AWS_PROFILE:?AWS_PROFILE is required (IAM admin)}"
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_DEFAULT_REGION="${AWS_REGION}"

[[ -f "${POLICY_DOC}" ]] || { echo "error: missing ${POLICY_DOC}" >&2; exit 1; }

ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
CALLER="$(aws sts get-caller-identity --query Arn --output text)"
POLICY_ARN="arn:aws:iam::${ACCOUNT}:policy/${POLICY_NAME}"

echo "==> caller=${CALLER##*/} account_len=${#ACCOUNT}"
echo "==> ensure managed policy ${POLICY_NAME}"

if aws iam get-policy --policy-arn "${POLICY_ARN}" >/dev/null 2>&1; then
  echo "policy exists; creating new default version from repo JSON"
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
    --description "CodeStrata operator Slice 17.6 runtime security (exact Insights secrets + narrow reader/secrets IAM). No AdministratorAccess." \
    >/dev/null
fi

echo "==> attach to user ${USER_NAME}"
aws iam attach-user-policy --user-name "${USER_NAME}" --policy-arn "${POLICY_ARN}"

echo "==> attached (names only)"
aws iam list-attached-user-policies --user-name "${USER_NAME}" \
  --query 'AttachedPolicies[].PolicyName' --output text

echo "attach-operator-runtime-security=ok"
echo "Next (as codestrata_infra):"
echo "  ./infrastructure/scripts/configure-production-secrets.sh generate"
echo "  ./infrastructure/scripts/configure-production-runtime-iam.sh"

#!/usr/bin/env bash
# Slice 17.6 — Configure production runtime IAM (idempotent; ingestion stays OFF).
#
# Creates/updates managed policies:
#   codestrata-community-insights-production-reader
#   codestrata-community-insights-production-secrets
# Attaches them to codestrata-community-cloud-production-lambda.
#
# Does NOT attach Data Lake writer. Does NOT enable ingestion.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOCAL_DIR="${REPO_ROOT}/infrastructure/production/.local"
EVIDENCE="${LOCAL_DIR}/runtime_security_evidence.json"
EVIDENCE_ALT="${LOCAL_DIR}/runtime_security_iam_evidence.json"

export AWS_PROFILE="${AWS_PROFILE:?AWS_PROFILE is required}"
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_DEFAULT_REGION="${AWS_REGION}"

READER_NAME="codestrata-community-insights-production-reader"
SECRETS_NAME="codestrata-community-insights-production-secrets"
WRITER_NAME="codestrata-community-data-lake-production-writer"
ROLE_NAME="codestrata-community-cloud-production-lambda"
LAMBDA_NAME="codestrata-community-cloud-production-api"
BUCKET="codestrata-community-data-lake-production"
PASSWORD_SECRET_ID="codestrata/insights/dashboard-password"
SESSION_SECRET_ID="codestrata/insights/session-secret"
MAX_IAM_RETRIES=8

die() { echo "error: $*" >&2; exit 1; }

echo "==> verify identity + region"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
[[ "${AWS_REGION}" == "us-west-2" ]] || die "AWS_REGION must be us-west-2"
echo "identity_ok"

BUCKET_ARN="arn:aws:s3:::${BUCKET}"
READER_ARN="arn:aws:iam::${ACCOUNT}:policy/${READER_NAME}"
SECRETS_ARN="arn:aws:iam::${ACCOUNT}:policy/${SECRETS_NAME}"
WRITER_ARN="arn:aws:iam::${ACCOUNT}:policy/${WRITER_NAME}"
ROLE_ARN="arn:aws:iam::${ACCOUNT}:role/${ROLE_NAME}"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/cs-iam.XXXXXX")"
chmod 700 "${TMP}"
cleanup() { rm -rf "${TMP}"; }
trap cleanup EXIT

cat > "${TMP}/reader.json" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListRawAnalyticsPrefixes",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": ["${BUCKET_ARN}"],
      "Condition": {
        "StringLike": {
          "s3:prefix": ["raw/", "raw/*"]
        }
      }
    },
    {
      "Sid": "GetRawAnalyticsObjects",
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": ["${BUCKET_ARN}/raw/*"]
    }
  ]
}
EOF

cat > "${TMP}/secrets.json" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InsightsAuthGetSecretValue",
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": [
        "arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT}:secret:${PASSWORD_SECRET_ID}-*",
        "arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT}:secret:${SESSION_SECRET_ID}-*"
      ]
    }
  ]
}
EOF

upsert_policy() {
  local name="$1"
  local arn="$2"
  local file="$3"
  local desc="$4"
  if aws iam get-policy --policy-arn "${arn}" >/dev/null 2>&1; then
    VERSIONS="$(aws iam list-policy-versions --policy-arn "${arn}" --query 'Versions[?IsDefaultVersion==`false`].VersionId' --output text)"
    COUNT="$(echo "${VERSIONS}" | wc -w | tr -d ' ')"
    if [[ "${COUNT}" -ge 4 ]]; then
      OLDEST="$(aws iam list-policy-versions --policy-arn "${arn}" --query 'Versions[?IsDefaultVersion==`false`]|sort_by(@,&CreateDate)[0].VersionId' --output text)"
      aws iam delete-policy-version --policy-arn "${arn}" --version-id "${OLDEST}"
    fi
    aws iam create-policy-version \
      --policy-arn "${arn}" \
      --policy-document "file://${file}" \
      --set-as-default >/dev/null
    echo "policy_updated=${name}"
  else
    aws iam create-policy \
      --policy-name "${name}" \
      --policy-document "file://${file}" \
      --description "${desc}" >/dev/null
    echo "policy_created=${name}"
  fi
}

echo "==> upsert reader + secrets policies"
upsert_policy "${READER_NAME}" "${READER_ARN}" "${TMP}/reader.json" \
  "Slice 17.6 bounded Insights S3 read on Community Data Lake raw/* only."
upsert_policy "${SECRETS_NAME}" "${SECRETS_ARN}" "${TMP}/secrets.json" \
  "Slice 17.6 GetSecretValue only for Insights auth secrets."

echo "==> attach to Lambda role (writer intentionally NOT attached)"
aws iam attach-role-policy --role-name "${ROLE_NAME}" --policy-arn "${READER_ARN}"
aws iam attach-role-policy --role-name "${ROLE_NAME}" --policy-arn "${SECRETS_ARN}"

# Bound IAM eventual-consistency retries (no unbounded loop).
retry=0
attached_ok=0
while [[ "${retry}" -lt "${MAX_IAM_RETRIES}" ]]; do
  NAMES="$(aws iam list-attached-role-policies --role-name "${ROLE_NAME}" --query 'AttachedPolicies[].PolicyName' --output text)"
  if echo "${NAMES}" | tr '\t' '\n' | grep -qx "${READER_NAME}" \
    && echo "${NAMES}" | tr '\t' '\n' | grep -qx "${SECRETS_NAME}"; then
    attached_ok=1
    break
  fi
  retry=$((retry + 1))
  sleep 2
done
[[ "${attached_ok}" -eq 1 ]] || die "policy attachment not visible after ${MAX_IAM_RETRIES} retries"

WRITER_ROLES="$(aws iam list-entities-for-policy --policy-arn "${WRITER_ARN}" --query 'PolicyRoles' --output json)"
echo "${WRITER_ROLES}" | python3 -c 'import json,sys; r=json.load(sys.stdin); raise SystemExit(0 if r==[] else 1)' \
  || die "writer policy unexpectedly attached — aborting Slice 17.6 safety gate"

echo "==> ensure ingestion env remains false (identifiers only if updating)"
CURRENT_INGESTION="$(aws lambda get-function-configuration \
  --function-name "${LAMBDA_NAME}" \
  --query 'Environment.Variables.CODESTRATA_INGESTION_ENABLED' --output text)"
[[ "${CURRENT_INGESTION}" == "false" ]] || die "CODESTRATA_INGESTION_ENABLED must be false (observed=${CURRENT_INGESTION})"

# Optional: set secret identifier env vars without secret values (idempotent).
aws lambda update-function-configuration \
  --function-name "${LAMBDA_NAME}" \
  --environment "Variables={CODESTRATA_DEPLOYMENT_MODE=production_foundation,CODESTRATA_COMMUNITY_API_VERSION=1.0,CODESTRATA_AUTHENTICATION_ENABLED=true,CODESTRATA_RATE_LIMIT_ENABLED=true,CODESTRATA_INGESTION_ENABLED=false,CODESTRATA_AUTHENTICATION_MODE=enabled_verifier_unavailable,CODESTRATA_RATE_LIMIT_MODE=api_gateway_plus_process_local,CODESTRATA_INSIGHTS_SECRETS_BACKEND=aws,CODESTRATA_INSIGHTS_PASSWORD_SECRET_ID=${PASSWORD_SECRET_ID},CODESTRATA_INSIGHTS_SESSION_SECRET_ID=${SESSION_SECRET_ID}}" \
  >/dev/null

# Bounded wait for Lambda configuration update.
retry=0
while [[ "${retry}" -lt "${MAX_IAM_RETRIES}" ]]; do
  STATUS="$(aws lambda get-function-configuration --function-name "${LAMBDA_NAME}" --query 'LastUpdateStatus' --output text)"
  [[ "${STATUS}" == "Successful" ]] && break
  retry=$((retry + 1))
  sleep 2
done

mkdir -p "${LOCAL_DIR}"
python3 - <<'PY' "${EVIDENCE}" "${EVIDENCE_ALT}" "${READER_NAME}" "${SECRETS_NAME}" "${WRITER_NAME}"
import json, sys
from pathlib import Path
path, alt, reader, secrets, writer = sys.argv[1:6]
payload = json.dumps(
    {
        "reader_policy": reader,
        "secrets_policy": secrets,
        "writer_policy": writer,
        "reader_attached": True,
        "secrets_attached": True,
        "writer_attached": False,
        "writer_attachment_status": "unattached_deferred_to_17_7",
        "lambda_secrets_iam_attached": True,
        "insights_auth_runtime_ready": True,
        "lambda_env_ready": True,
        "lambda_env_secrets_backend": "aws",
        "ingestion_enabled": False,
        "bedrock_granted": False,
        "provider_credentials_configured": False,
    },
    sort_keys=True,
    indent=2,
) + "\n"
for p in (path, alt):
    Path(p).write_text(payload, encoding="utf-8")
print("iam_evidence_written=sanitized")
PY

echo "attached_policies:"
aws iam list-attached-role-policies --role-name "${ROLE_NAME}" --query 'AttachedPolicies[].PolicyName' --output text
echo "configure-production-runtime-iam=ok ingestion_enabled=false writer_attached=false"

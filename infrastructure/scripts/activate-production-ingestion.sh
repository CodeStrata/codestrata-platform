#!/usr/bin/env bash
# Slice 17.7 — Activate production ingestion (attach writer, then enable env).
#
# - Attaches Data Lake writer policy to Lambda role (idempotent)
# - Ensures GetSecretValue policy for community credentials secret
# - Verifies writer attachment with bounded retries BEFORE enabling env
# - Updates Lambda env identifiers only (no secret values)
# - Keeps Insights reader/secrets policies attached
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOCAL_DIR="${REPO_ROOT}/infrastructure/production/.local"
EVIDENCE="${LOCAL_DIR}/sv17-7-activation.json"
EVIDENCE_ALIAS="${LOCAL_DIR}/ingestion_activation_evidence.json"

export AWS_PROFILE="${AWS_PROFILE:?AWS_PROFILE is required}"
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_DEFAULT_REGION="${AWS_REGION}"

WRITER_NAME="codestrata-community-data-lake-production-writer"
INGEST_SECRETS_NAME="codestrata-community-ingestion-production-secrets"
READER_NAME="codestrata-community-insights-production-reader"
INSIGHTS_SECRETS_NAME="codestrata-community-insights-production-secrets"
ROLE_NAME="codestrata-community-cloud-production-lambda"
LAMBDA_NAME="codestrata-community-cloud-production-api"
BUCKET="codestrata-community-data-lake-production"
CREDENTIALS_SECRET_ID="${CODESTRATA_COMMUNITY_CREDENTIALS_SECRET_ID:-codestrata/community/client-credentials}"
MAX_IAM_RETRIES=8

die() { echo "error: $*" >&2; exit 1; }

echo "==> verify identity + region"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
[[ "${AWS_REGION}" == "us-west-2" ]] || die "AWS_REGION must be us-west-2"
echo "identity_ok"

WRITER_ARN="arn:aws:iam::${ACCOUNT}:policy/${WRITER_NAME}"
INGEST_SECRETS_ARN="arn:aws:iam::${ACCOUNT}:policy/${INGEST_SECRETS_NAME}"
ROLE_ARN="arn:aws:iam::${ACCOUNT}:role/${ROLE_NAME}"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/cs-ingest-activate.XXXXXX")"
chmod 700 "${TMP}"
cleanup() { rm -rf "${TMP}"; }
trap cleanup EXIT

cat > "${TMP}/ingest_secrets.json" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CommunityCredentialsGetSecretValue",
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": [
        "arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT}:secret:${CREDENTIALS_SECRET_ID}-*"
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
    return 0
  fi
  if aws iam create-policy \
    --policy-name "${name}" \
    --policy-document "file://${file}" \
    --description "${desc}" >/dev/null 2>"${TMP}/create_policy.err"; then
    echo "policy_created=${name}"
    return 0
  fi
  echo "create_policy_failed=${name}" >&2
  return 1
}

echo "==> upsert ingestion secrets GetSecretValue policy"
INGEST_SECRETS_ATTACHED_VIA=""
if upsert_policy "${INGEST_SECRETS_NAME}" "${INGEST_SECRETS_ARN}" "${TMP}/ingest_secrets.json" \
  "Slice 17.7 GetSecretValue only for Community client credential fingerprints."; then
  INGEST_SECRETS_ATTACHED_VIA="managed"
else
  echo "warn: managed ingestion-secrets CreatePolicy unavailable; using inline PutRolePolicy"
  INLINE_NAME="codestrata-community-cloud-production-ingestion-secrets"
  aws iam put-role-policy \
    --role-name "${ROLE_NAME}" \
    --policy-name "${INLINE_NAME}" \
    --policy-document "file://${TMP}/ingest_secrets.json"
  INGEST_SECRETS_ATTACHED_VIA="inline:${INLINE_NAME}"
fi

echo "==> attach writer (+ managed ingestion secrets when available) to Lambda role"
aws iam get-policy --policy-arn "${WRITER_ARN}" >/dev/null \
  || die "writer policy missing — apply community-data-lake module first"
aws iam attach-role-policy --role-name "${ROLE_NAME}" --policy-arn "${WRITER_ARN}"
if [[ "${INGEST_SECRETS_ATTACHED_VIA}" == "managed" ]]; then
  aws iam attach-role-policy --role-name "${ROLE_NAME}" --policy-arn "${INGEST_SECRETS_ARN}"
fi

# Bound IAM eventual-consistency retries — assert writer before enabling env.
retry=0
writer_ok=0
while [[ "${retry}" -lt "${MAX_IAM_RETRIES}" ]]; do
  NAMES="$(aws iam list-attached-role-policies --role-name "${ROLE_NAME}" --query 'AttachedPolicies[].PolicyName' --output text)"
  INLINE_NAMES="$(aws iam list-role-policies --role-name "${ROLE_NAME}" --query 'PolicyNames' --output text)"
  secrets_ok=0
  if [[ "${INGEST_SECRETS_ATTACHED_VIA}" == "managed" ]]; then
    echo "${NAMES}" | tr '\t' '\n' | grep -qx "${INGEST_SECRETS_NAME}" && secrets_ok=1
  else
    echo "${INLINE_NAMES}" | tr '\t' '\n' | grep -qx "codestrata-community-cloud-production-ingestion-secrets" && secrets_ok=1
  fi
  if echo "${NAMES}" | tr '\t' '\n' | grep -qx "${WRITER_NAME}" && [[ "${secrets_ok}" -eq 1 ]]; then
    writer_ok=1
    break
  fi
  retry=$((retry + 1))
  sleep 2
done
[[ "${writer_ok}" -eq 1 ]] || die "writer/ingestion-secrets attachment not visible after ${MAX_IAM_RETRIES} retries"

# Preserve Insights policies if present (do not detach).
INSIGHTS_OK=0
if echo "${NAMES}" | tr '\t' '\n' | grep -qx "${READER_NAME}" \
  && echo "${NAMES}" | tr '\t' '\n' | grep -qx "${INSIGHTS_SECRETS_NAME}"; then
  INSIGHTS_OK=1
fi

echo "==> update Lambda env (identifiers only; writer already verified)"
CURRENT_ENV_JSON="$(aws lambda get-function-configuration \
  --function-name "${LAMBDA_NAME}" \
  --query 'Environment.Variables' --output json)"

python3 - <<'PY' "${CURRENT_ENV_JSON}" "${TMP}/env.json" "${BUCKET}" "${CREDENTIALS_SECRET_ID}"
import json, sys
from pathlib import Path
current_raw, out_path, bucket, secret_id = sys.argv[1:5]
current = json.loads(current_raw) if current_raw and current_raw != "null" else {}
if not isinstance(current, dict):
    current = {}
current["CODESTRATA_DEPLOYMENT_MODE"] = "production_ingestion"
current["CODESTRATA_INGESTION_ENABLED"] = "true"
current["CODESTRATA_INGESTION_WIRE"] = "true"
current["CODESTRATA_DATA_LAKE_ADAPTER"] = "s3"
current["CODESTRATA_DATA_LAKE_BUCKET"] = bucket
current["CODESTRATA_COMMUNITY_CREDENTIALS_SECRET_ID"] = secret_id
current["CODESTRATA_AUTHENTICATION_MODE"] = "enabled_aws_credentials"
# Never inject secret values into Lambda env.
Path(out_path).write_text(json.dumps({"Variables": current}, sort_keys=True), encoding="utf-8")
print("env_payload_prepared=true")
PY

aws lambda update-function-configuration \
  --function-name "${LAMBDA_NAME}" \
  --environment "file://${TMP}/env.json" >/dev/null

VERIFY_INGESTION="$(aws lambda get-function-configuration \
  --function-name "${LAMBDA_NAME}" \
  --query 'Environment.Variables.CODESTRATA_INGESTION_ENABLED' --output text)"
VERIFY_WIRE="$(aws lambda get-function-configuration \
  --function-name "${LAMBDA_NAME}" \
  --query 'Environment.Variables.CODESTRATA_INGESTION_WIRE' --output text)"
VERIFY_BUCKET="$(aws lambda get-function-configuration \
  --function-name "${LAMBDA_NAME}" \
  --query 'Environment.Variables.CODESTRATA_DATA_LAKE_BUCKET' --output text)"

[[ "${VERIFY_INGESTION}" == "true" ]] || die "ingestion env not true after update"
[[ "${VERIFY_WIRE}" == "true" ]] || die "ingestion wire env not true after update"
[[ "${VERIFY_BUCKET}" == "${BUCKET}" ]] || die "data lake bucket env mismatch"

python3 - <<'PY' "${EVIDENCE}" "${WRITER_NAME}" "${INGEST_SECRETS_ATTACHED_VIA}" "${INSIGHTS_OK}" "${BUCKET}"
import json, sys
from pathlib import Path
path, writer, ingest_secrets, insights_ok, bucket = sys.argv[1:6]
payload = json.dumps(
    {
        "evidence_type": "activation",
        "sanitized": True,
        "data_lake_bucket_configured": True,
        "data_lake_bucket_name_set": True,
        "deployment_mode": "production_ingestion",
        "ingestion_enabled": True,
        "ingestion_wire": True,
        "insights_policies_retained": insights_ok == "1",
        "ingestion_secrets_policy": ingest_secrets,
        "writer_attached": True,
        "writer_policy_attached": True,
        "writer_policy_name": writer,
        "writer_verified_before_enable": True,
        "secret_values_in_evidence": False,
        "secret_values_in_lambda_env": False,
    },
    sort_keys=True,
    indent=2,
) + "\n"
Path(path).parent.mkdir(parents=True, exist_ok=True)
Path(path).write_text(payload, encoding="utf-8")
alias = Path(path).with_name("ingestion_activation_evidence.json")
alias.write_text(payload, encoding="utf-8")
print("evidence_written=sanitized")
PY

echo "activate-production-ingestion=ok"
echo "status writer_attached=true ingestion_enabled=true wire=true insights_retained=${INSIGHTS_OK} secrets_via=${INGEST_SECRETS_ATTACHED_VIA}"
echo "NOTE: secret values were not written to evidence or Lambda env"

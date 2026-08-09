#!/usr/bin/env bash
# Slice 17.7 — Configure production Community ingestion client credentials.
#
# Creates/updates Secrets Manager secret:
#   codestrata/community/client-credentials
#
# Secret stores fingerprint JSON only — never raw tokens.
# Prints the generated token ONCE to stdout for the owner.
# Evidence files contain fingerprint metadata only.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOCAL_DIR="${REPO_ROOT}/infrastructure/production/.local"
EVIDENCE="${LOCAL_DIR}/ingestion_credentials_evidence.json"

export AWS_PROFILE="${AWS_PROFILE:?AWS_PROFILE is required}"
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_DEFAULT_REGION="${AWS_REGION}"

SECRET_ID="${CODESTRATA_COMMUNITY_CREDENTIALS_SECRET_ID:-codestrata/community/client-credentials}"
CLIENT_TYPE="${CLIENT_TYPE:-codestrata_cli}"
CLIENT_ID="${CLIENT_ID:-client-community-cli-production}"
CREDENTIAL_ID="${CREDENTIAL_ID:-cred-community-cli-production}"
RATE_LIMIT_SCOPE_ID="${RATE_LIMIT_SCOPE_ID:-rlscope-community-cli-production}"
MODE="${1:-generate}"  # generate | update-existing-fingerprint-only (idempotent put)

TMPDIR_SAFE=""
cleanup() {
  if [[ -n "${TMPDIR_SAFE}" && -d "${TMPDIR_SAFE}" ]]; then
    rm -rf "${TMPDIR_SAFE}"
  fi
}
trap cleanup EXIT

die() { echo "error: $*" >&2; exit 1; }

echo "==> verify identity + region"
IDENTITY="$(aws sts get-caller-identity --output json)"
ACCOUNT="$(printf '%s' "${IDENTITY}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["Account"])')"
ARN="$(printf '%s' "${IDENTITY}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["Arn"])')"
[[ "${AWS_REGION}" == "us-west-2" ]] || die "AWS_REGION must be us-west-2"
echo "identity_ok account_len=${#ACCOUNT} arn_suffix=${ARN##*/}"

mkdir -p "${LOCAL_DIR}"
TMPDIR_SAFE="$(mktemp -d "${TMPDIR:-/tmp}/cs-ingest-creds.XXXXXX")"
chmod 700 "${TMPDIR_SAFE}"

python3 - <<'PY' "${MODE}" "${TMPDIR_SAFE}" "${SECRET_ID}" "${CLIENT_TYPE}" "${CLIENT_ID}" "${CREDENTIAL_ID}" "${RATE_LIMIT_SCOPE_ID}"
import hashlib, json, secrets, sys
from pathlib import Path

mode, tmp, secret_id, client_type, client_id, credential_id, rate_limit_scope_id = sys.argv[1:8]
tmp_path = Path(tmp)

POLICY_TOKEN = "community-authentication-policy:1.0"
FORMAT_VERSION = "1"
PREFIX = "cscc_v1_"

def fingerprint_credential(token: str) -> str:
    material = "|".join((POLICY_TOKEN, FORMAT_VERSION, PREFIX, token))
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return f"cred:{digest}"

# URL-safe body after prefix; keep within credential length bounds.
body = secrets.token_urlsafe(32).replace("-", "x").replace("_", "y")[:40]
token = f"{PREFIX}{body}"
fp = fingerprint_credential(token)

payload = {
    "credentials": [
        {
            "allowed_route_groups": ["ingestion"],
            "client_id": client_id,
            "client_type": client_type,
            "credential_fingerprint": fp,
            "credential_id": credential_id,
            "credential_version": "1",
            "rate_limit_scope_id": rate_limit_scope_id,
            "status": "active",
        }
    ]
}
secret_text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
(tmp_path / "credentials.json").write_text(secret_text, encoding="utf-8")
(tmp_path / "token.once").write_text(token, encoding="utf-8")
(tmp_path / "meta.json").write_text(
    json.dumps(
        {
            "client_id": client_id,
            "client_type": client_type,
            "credential_fingerprint_prefix": fp[:12],
            "credential_id": credential_id,
            "mode": mode,
            "secret_id": secret_id,
            "status": "active",
        },
        sort_keys=True,
    ),
    encoding="utf-8",
)
print("credential_material_prepared=true")
PY

put_or_create() {
  local name="$1"
  local file="$2"
  local desc="$3"
  if aws secretsmanager describe-secret --secret-id "${name}" >/dev/null 2>&1; then
    aws secretsmanager put-secret-value \
      --secret-id "${name}" \
      --secret-string "file://${file}" >/dev/null
    echo "updated=${name}"
  else
    aws secretsmanager create-secret \
      --name "${name}" \
      --description "${desc}" \
      --secret-string "file://${file}" \
      --tags Key=Project,Value=codestrata Key=Environment,Value=production Key=Slice,Value=17.7 \
      >/dev/null
    echo "created=${name}"
  fi
}

echo "==> upsert fingerprint secret (values via file://; token not echoed here)"
put_or_create "${SECRET_ID}" "${TMPDIR_SAFE}/credentials.json" \
  "Community Cloud client credential fingerprints (Slice 17.7). Fingerprints only; raw tokens out of Git/IaC."

echo ""
echo "=========================================="
echo "OWNER ONE-TIME COMMUNITY CLIENT TOKEN (copy now)"
echo "=========================================="
cat "${TMPDIR_SAFE}/token.once"
echo ""
echo "=========================================="
echo "(token is not written to evidence files)"
echo ""

python3 - <<'PY' "${EVIDENCE}" "${SECRET_ID}" "${TMPDIR_SAFE}/meta.json"
import json, sys
from pathlib import Path
path, secret_id, meta_path = sys.argv[1:4]
meta = json.loads(Path(meta_path).read_text(encoding="utf-8"))
payload = json.dumps(
    {
        "client_id": meta["client_id"],
        "client_type": meta["client_type"],
        "credential_fingerprint_prefix": meta["credential_fingerprint_prefix"],
        "credential_id": meta["credential_id"],
        "secret_id": secret_id,
        "secret_value_storage": "secrets_manager_fingerprints_only",
        "secrets_configured": True,
        "status": meta["status"],
        "token_in_evidence": False,
        "values_in_git": False,
        "values_in_opentofu": False,
    },
    sort_keys=True,
    indent=2,
) + "\n"
Path(path).parent.mkdir(parents=True, exist_ok=True)
Path(path).write_text(payload, encoding="utf-8")
print("evidence_written=sanitized_fingerprint_metadata")
PY

echo "configure-production-ingestion-credentials=ok region=${AWS_REGION}"
echo "NOTE: raw token was printed once above and was not written to evidence"

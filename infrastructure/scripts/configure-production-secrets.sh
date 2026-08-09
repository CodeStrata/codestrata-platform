#!/usr/bin/env bash
# Slice 17.6 — Configure production Insights auth secrets (values never logged to reports).
#
# Creates/updates:
#   codestrata/insights/dashboard-password  (scrypt verifier JSON preferred)
#   codestrata/insights/session-secret      (cryptographic signing material)
#
# Does NOT write secret values to Git, OpenTofu, or verification reports.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOCAL_DIR="${REPO_ROOT}/infrastructure/production/.local"
EVIDENCE="${LOCAL_DIR}/secrets_evidence.json"
EVIDENCE_ALT="${LOCAL_DIR}/runtime_security_secrets_evidence.json"

export AWS_PROFILE="${AWS_PROFILE:?AWS_PROFILE is required}"
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_DEFAULT_REGION="${AWS_REGION}"

PASSWORD_SECRET_ID="codestrata/insights/dashboard-password"
SESSION_SECRET_ID="codestrata/insights/session-secret"
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
TMPDIR_SAFE="$(mktemp -d "${TMPDIR:-/tmp}/cs-secrets.XXXXXX")"
chmod 700 "${TMPDIR_SAFE}"

MODE="${1:-generate}"
# Modes: generate | prompt-password

python3 - <<'PY' "${MODE}" "${TMPDIR_SAFE}" "${PASSWORD_SECRET_ID}" "${SESSION_SECRET_ID}"
import hashlib, base64, json, os, secrets, sys, getpass
from pathlib import Path

mode, tmp, password_id, session_id = sys.argv[1:5]
tmp_path = Path(tmp)

SCRYPT_N, SCRYPT_R, SCRYPT_P, SCRYPT_DKLEN = 2**14, 8, 1, 64

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_DKLEN,
    )
    payload = {
        "algorithm": "scrypt",
        "hash_b64": base64.b64encode(derived).decode("ascii"),
        "n": SCRYPT_N,
        "p": SCRYPT_P,
        "r": SCRYPT_R,
        "salt_b64": base64.b64encode(salt).decode("ascii"),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))

if mode == "prompt-password":
    password = getpass.getpass("Dashboard password (not echoed): ")
    confirm = getpass.getpass("Confirm dashboard password: ")
    if password != confirm or len(password) < 16:
        raise SystemExit("password mismatch or too short (min 16)")
else:
    # URL-safe high entropy password for owner one-time display
    password = secrets.token_urlsafe(24)

session_secret = secrets.token_urlsafe(48)
verifier = hash_password(password)

(tmp_path / "password_verifier.json").write_text(verifier, encoding="utf-8")
(tmp_path / "session_secret.txt").write_text(session_secret, encoding="utf-8")
# Owner-visible password file — deleted on cleanup; printed once below outside Python if generate
(tmp_path / "dashboard_password.once").write_text(password, encoding="utf-8")
(tmp_path / "meta.json").write_text(
    json.dumps(
        {
            "password_secret_id": password_id,
            "session_secret_id": session_id,
            "password_format": "scrypt_verifier_json",
            "session_format": "token_urlsafe_48",
            "mode": mode,
        },
        sort_keys=True,
    ),
    encoding="utf-8",
)
print("secret_material_prepared=true")
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
      --tags Key=Project,Value=codestrata Key=Environment,Value=production Key=Slice,Value=17.6 \
      >/dev/null
    echo "created=${name}"
  fi
}

echo "==> upsert secrets (values via file://; not echoed)"
put_or_create "${PASSWORD_SECRET_ID}" "${TMPDIR_SAFE}/password_verifier.json" \
  "Community Insights dashboard password scrypt verifier (Slice 17.6). Value out of Git/IaC."
put_or_create "${SESSION_SECRET_ID}" "${TMPDIR_SAFE}/session_secret.txt" \
  "Community Insights session signing secret (Slice 17.6). Value out of Git/IaC."

# One-time owner display for generated dashboard password only (never session secret).
if [[ "${MODE}" == "generate" ]]; then
  echo ""
  echo "=========================================="
  echo "OWNER ONE-TIME DASHBOARD PASSWORD (copy now)"
  echo "=========================================="
  cat "${TMPDIR_SAFE}/dashboard_password.once"
  echo ""
  echo "=========================================="
  echo "(session secret intentionally not displayed)"
  echo ""
fi

python3 - <<'PY' "${EVIDENCE}" "${EVIDENCE_ALT}" "${PASSWORD_SECRET_ID}" "${SESSION_SECRET_ID}"
import json, sys
from pathlib import Path
path, alt, password_id, session_id = sys.argv[1:5]
payload = json.dumps(
    {
        "secrets_configured": True,
        "secrets_created": True,
        "password_secret_id": password_id,
        "session_secret_id": session_id,
        "password_format": "scrypt_verifier_json",
        "session_format": "token_urlsafe_48",
        "secret_value_storage": "secrets_manager_only",
        "values_in_git": False,
        "values_in_opentofu": False,
        "values_in_evidence": False,
    },
    sort_keys=True,
    indent=2,
) + "\n"
for p in (path, alt):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(payload, encoding="utf-8")
print("evidence_written=sanitized")
PY

echo "configure-production-secrets=ok region=${AWS_REGION}"
echo "NOTE: secret values were not written to evidence files"

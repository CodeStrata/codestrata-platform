#!/usr/bin/env bash
# Health-only smoke check against an explicit API base URL.
# Does not call ingestion endpoints. Does not use authentication tokens.
set -euo pipefail

BASE_URL="${1:-}"
TIMEOUT_SECONDS="${SMOKE_TIMEOUT_SECONDS:-10}"

usage() {
  cat <<'EOF'
Usage: smoke-health.sh <api-base-url>

Calls GET {base}/api/v1/health and verifies status 200 plus safe JSON fields.
Does not call ingestion endpoints. Does not require an auth token.
EOF
}

if [[ -z "${BASE_URL}" || "${BASE_URL}" == "-h" || "${BASE_URL}" == "--help" ]]; then
  usage
  exit 2
fi

# Strip trailing slash.
BASE_URL="${BASE_URL%/}"
HEALTH_URL="${BASE_URL}/api/v1/health"

command -v curl >/dev/null 2>&1 || {
  echo "error: curl is required" >&2
  exit 1
}
command -v python3 >/dev/null 2>&1 || {
  echo "error: python3 is required" >&2
  exit 1
}

TMP_BODY="$(mktemp)"
trap 'rm -f "${TMP_BODY}"' EXIT

HTTP_CODE="$(
  curl -sS \
    --max-time "${TIMEOUT_SECONDS}" \
    -o "${TMP_BODY}" \
    -w "%{http_code}" \
    -H "Accept: application/json" \
    "${HEALTH_URL}"
)"

if [[ "${HTTP_CODE}" != "200" ]]; then
  echo "error: expected HTTP 200 from ${HEALTH_URL}, got ${HTTP_CODE}" >&2
  exit 1
fi

python3 - "${TMP_BODY}" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as fh:
    raw = fh.read()

# Refuse to echo bodies that look secret-like.
lower = raw.lower()
for needle in ("authorization", "bearer ", "aws_secret", "cscc_v1_", "private_key"):
    if needle in lower:
        print("error: response contained unexpected secret-like content; not dumping", file=sys.stderr)
        sys.exit(1)

body = json.loads(raw)
required = {
    "api_version": "v1",
    "schema_version": "1.0",
    "service": "codestrata-community-cloud-api",
    "status": "ok",
}
for key, expected in required.items():
    if body.get(key) != expected:
        print(f"error: field {key!r} expected {expected!r}, got {body.get(key)!r}", file=sys.stderr)
        sys.exit(1)
if "application_version" not in body or not isinstance(body["application_version"], str):
    print("error: application_version missing or not a string", file=sys.stderr)
    sys.exit(1)
print("health ok")
PY

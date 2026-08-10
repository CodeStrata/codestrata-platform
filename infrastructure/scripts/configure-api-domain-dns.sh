#!/usr/bin/env bash
# Slice 17.14 — Upsert Cloudflare DNS for api.codestrata.ai (DNS-only / not proxied).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PROD="${ROOT}/infrastructure/production"
LOCAL="${PROD}/.local"
MODE="${1:-all}"

export AWS_PROFILE="${AWS_PROFILE:-codestrata_infra}"
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_DEFAULT_REGION="${AWS_REGION}"

die() { echo "error: $*" >&2; exit 1; }
mkdir -p "${LOCAL}"

[[ -n "${CLOUDFLARE_API_TOKEN:-}" ]] || die "CLOUDFLARE_API_TOKEN is required (not stored in git)"

ZONE_ID="${CLOUDFLARE_ZONE_ID:-}"
if [[ -z "${ZONE_ID}" ]]; then
  ZONE_ID="$(curl -sS -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
    "https://api.cloudflare.com/client/v4/zones?name=codestrata.ai" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); r=d.get("result") or []; print(r[0]["id"] if r else "")')"
  [[ -n "${ZONE_ID}" ]] || die "could not resolve Cloudflare zone id for codestrata.ai"
fi

upsert_cname() {
  local name="$1" content="$2"
  name="${name%.}"
  content="${content%.}"
  local existing
  existing="$(curl -sS -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
    "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records?type=CNAME&name=${name}" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); r=d.get("result") or []; print(r[0]["id"] if r else "")')"
  local body
  body="$(NAME="${name}" CONTENT="${content}" python3 - <<'PY'
import json, os
print(json.dumps({
  "type": "CNAME",
  "name": os.environ["NAME"],
  "content": os.environ["CONTENT"],
  "ttl": 300,
  "proxied": False,
}))
PY
)"
  if [[ -n "${existing}" ]]; then
    curl -sS -X PUT -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
      -H "Content-Type: application/json" --data "${body}" \
      "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records/${existing}" \
      | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get("success"), d; print("updated")'
  else
    curl -sS -X POST -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
      -H "Content-Type: application/json" --data "${body}" \
      "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
      | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get("success"), d; print("created")'
  fi
  echo "cname=${name}"
}

upsert_validation() {
  cd "${PROD}"
  tofu output -json acm_validation_records > "${LOCAL}/sv17-14-acm-validation.raw.json"
  python3 - <<PY
import json
from pathlib import Path
raw = json.loads(Path("${LOCAL}/sv17-14-acm-validation.raw.json").read_text())
recs = raw["value"] if isinstance(raw, dict) and "value" in raw else raw
assert isinstance(recs, list) and recs, "acm_validation_records empty"
Path("${LOCAL}/sv17-14-acm-validation.json").write_text(json.dumps(recs, indent=2) + "\n")
print(f"validation_records={len(recs)}")
for r in recs:
    assert r.get("type") == "CNAME", r
    assert r.get("name") and r.get("value"), r
PY
  while IFS= read -r rec; do
    name="$(REC="${rec}" python3 -c 'import json,os; print(json.loads(os.environ["REC"])["name"])')"
    value="$(REC="${rec}" python3 -c 'import json,os; print(json.loads(os.environ["REC"])["value"])')"
    upsert_cname "${name}" "${value}"
  done < <(python3 -c 'import json; from pathlib import Path
recs=json.loads(Path("'"${LOCAL}"'/sv17-14-acm-validation.json").read_text())
[print(json.dumps(r)) for r in recs]')
}

upsert_api() {
  cd "${PROD}"
  TARGET="$(tofu output -raw api_custom_domain_target 2>/dev/null || true)"
  [[ -n "${TARGET}" ]] || die "api_custom_domain_target empty — apply custom domain first"
  upsert_cname "api.codestrata.ai" "${TARGET}"
  python3 - <<PY
import json
from pathlib import Path
Path("${LOCAL}/sv17-14-dns.json").write_text(json.dumps({
  "schema": "sv17-14-dns-evidence:1.0",
  "hostname": "api.codestrata.ai",
  "proxied": False,
  "dns_only": True,
  "target_class": "api_gateway_regional_domain",
  "zone": "codestrata.ai",
}, indent=2) + "\n")
PY
}

case "${MODE}" in
  validation) upsert_validation ;;
  api) upsert_api ;;
  all) upsert_validation; upsert_api ;;
  *) die "usage: $0 [validation|api|all]" ;;
esac

echo "configure-api-domain-dns=${MODE}=ok"

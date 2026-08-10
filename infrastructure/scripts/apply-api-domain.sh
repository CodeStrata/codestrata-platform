#!/usr/bin/env bash
# Slice 17.14 — Apply ACM + API Gateway custom domain for api.codestrata.ai.
#
# Phases:
#   1) Request ACM certificate (targeted apply)
#   2) Upsert Cloudflare ACM validation CNAMEs (requires CLOUDFLARE_API_TOKEN)
#   3) Complete validation + domain + mapping
#   4) Upsert api.codestrata.ai DNS-only CNAME
#   5) Zero-drift plan check
#
# Prerequisites: CodeStrataOperatorApiDomain attached to codestrata_infra.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PROD="${ROOT}/infrastructure/production"
LOCAL="${PROD}/.local"

export AWS_PROFILE="${AWS_PROFILE:-codestrata_infra}"
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_DEFAULT_REGION="${AWS_REGION}"

die() { echo "error: $*" >&2; exit 1; }
mkdir -p "${LOCAL}"
cd "${PROD}"

command -v tofu >/dev/null || die "opentofu (tofu) required"
[[ -f backend.hcl ]] || die "missing backend.hcl"

echo "==> tofu init"
tofu init -input=false -backend-config=backend.hcl >/dev/null

echo "==> phase1: ACM certificate"
tofu apply -input=false -auto-approve \
  -target=module.community_cloud_api.aws_acm_certificate.api_custom_domain \
  2>&1 | tee "${LOCAL}/sv17-14-acm-apply.log" | tail -30

echo "==> phase2: Cloudflare ACM validation DNS"
[[ -n "${CLOUDFLARE_API_TOKEN:-}" ]] || die "CLOUDFLARE_API_TOKEN required for DNS validation"
bash "${SCRIPT_DIR}/configure-api-domain-dns.sh" validation

echo "==> phase3: validation + custom domain + mapping"
tofu apply -input=false -auto-approve 2>&1 | tee "${LOCAL}/sv17-14-domain-apply.log" | tail -40

echo "==> phase4: api.codestrata.ai DNS-only CNAME"
bash "${SCRIPT_DIR}/configure-api-domain-dns.sh" api

echo "==> phase5: zero-drift plan"
set +e
tofu plan -input=false -detailed-exitcode -out="${LOCAL}/sv17-14-post.tfplan" \
  >"${LOCAL}/sv17-14-post.stdout.txt" 2>"${LOCAL}/sv17-14-post.stderr.txt"
rc=$?
set -e
if [[ "${rc}" -eq 2 ]]; then
  die "post-apply drift detected (exit 2)"
elif [[ "${rc}" -ne 0 ]]; then
  die "tofu plan failed rc=${rc}"
fi

python3 - <<PY
import json
from pathlib import Path
Path("${LOCAL}/sv17-14-apply-evidence.json").write_text(json.dumps({
  "schema": "sv17-14-api-domain-apply-evidence:1.0",
  "public_api_hostname": "api.codestrata.ai",
  "region": "us-west-2",
  "execute_api_retained": True,
  "dns_proxied": False,
  "zero_drift": True,
}, indent=2) + "\n")
PY

echo "apply-api-domain=ok zero_drift=true"

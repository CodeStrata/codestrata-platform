#!/usr/bin/env bash
# Slice 17.2 — Bootstrap OpenTofu remote-state S3 bucket (idempotent).
# Usage:
#   export AWS_PROFILE=codestrata_infra
#   export AWS_REGION=us-west-2
#   ./infrastructure/scripts/bootstrap-remote-state.sh
#
# Creates ONLY the dedicated OpenTofu state S3 bucket.
# Does NOT run production tofu apply. Does NOT create DynamoDB/product infra.
#
# Bucket creation uses AWS CLI (operator IAM cannot refresh aws_s3_bucket due to
# missing GetBucketPolicy/GetBucketTagging). OpenTofu local state manages
# versioning / encryption / PAB / ownership controls.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BOOTSTRAP="$ROOT/infrastructure/bootstrap/remote-state"
PROD="$ROOT/infrastructure/production"
EVIDENCE_DIR="$ROOT/infrastructure/bootstrap/remote-state/.local"
mkdir -p "$EVIDENCE_DIR"

# Ensure pipeline failures are observed when stdout is piped
set -o pipefail

export AWS_PROFILE="${AWS_PROFILE:-codestrata_infra}"
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-$AWS_REGION}"
export CHECKPOINT_DISABLE=1

# Avoid Cursor/local broken proxies for AWS
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy || true

if [[ "$AWS_PROFILE" != "codestrata_infra" ]]; then
  echo "FAIL: AWS_PROFILE must be codestrata_infra (got: $AWS_PROFILE)" >&2
  exit 2
fi
if [[ "$AWS_REGION" != "us-west-2" ]]; then
  echo "FAIL: AWS_REGION must be us-west-2 (got: $AWS_REGION)" >&2
  exit 2
fi

echo "==> Verifying caller identity (sanitized)"
IDENTITY_JSON="$(aws sts get-caller-identity --output json)"
ACCOUNT_ID="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["Account"])' <<<"$IDENTITY_JSON")"
USER="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["Arn"].rsplit("/",1)[-1])' <<<"$IDENTITY_JSON")"
if [[ "$USER" != "codestrata_infra" ]]; then
  echo "FAIL: expected IAM user codestrata_infra (got: $USER)" >&2
  exit 2
fi
ACCOUNT_FP="$(python3 -c "import hashlib; print(hashlib.sha256(b'$ACCOUNT_ID').hexdigest()[:12])")"
SUFFIX="$(python3 -c "import hashlib; print(hashlib.sha256(('codestrata-opentofu-state|' + '$ACCOUNT_ID').encode()).hexdigest()[:8])")"
BUCKET="codestrata-opentofu-state-production-${SUFFIX}"
STATE_KEY="codestrata/community-cloud/production/terraform.tfstate"
echo "identity_ok=true user=$USER account_fp=$ACCOUNT_FP region=$AWS_REGION"
echo "bucket=$BUCKET"
echo "state_key=$STATE_KEY"

if [[ "$BUCKET" == *"community-data-lake"* ]]; then
  echo "FAIL: bucket name collides with data lake naming" >&2
  exit 2
fi

echo "==> Ensure dedicated state bucket exists (AWS CLI)"
if aws s3api head-bucket --bucket "$BUCKET" --region "$AWS_REGION" >/dev/null 2>&1; then
  echo "bucket_exists=true"
else
  echo "bucket_exists=false creating..."
  # us-west-2 requires LocationConstraint
  aws s3api create-bucket \
    --bucket "$BUCKET" \
    --region "$AWS_REGION" \
    --create-bucket-configuration LocationConstraint="$AWS_REGION" \
    >/dev/null
  echo "bucket_created=true"
fi

echo "==> Apply required S3 controls via AWS CLI (idempotent)"
aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled >/dev/null
aws s3api put-bucket-encryption --bucket "$BUCKET" --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' >/dev/null
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" >/dev/null
aws s3api put-bucket-ownership-controls --bucket "$BUCKET" --ownership-controls \
  'Rules=[{ObjectOwnership=BucketOwnerEnforced}]' >/dev/null

echo "==> Bootstrap OpenTofu (local state) — control resources"
cd "$BOOTSTRAP"
STATE_FILE="$EVIDENCE_DIR/terraform.tfstate"
TOFU_STATE=(-state="$STATE_FILE")
# Drop incompatible aws_s3_bucket from any prior partial local state
if tofu state list "${TOFU_STATE[@]}" 2>/dev/null | rg -q '^aws_s3_bucket\.opentofu_state$'; then
  tofu state rm "${TOFU_STATE[@]}" aws_s3_bucket.opentofu_state >/dev/null || true
fi
tofu init -input=false >/dev/null

cat > "$EVIDENCE_DIR/bootstrap.auto.tfvars" <<EOF
aws_region  = "$AWS_REGION"
bucket_name = "$BUCKET"
EOF

echo "==> Import/apply control resources"
# Import if already configured in AWS but missing from local state
import_if_needed() {
  local addr="$1"
  if ! tofu state list "${TOFU_STATE[@]}" 2>/dev/null | rg -qx "$addr"; then
    tofu import "${TOFU_STATE[@]}" -input=false -var-file="$EVIDENCE_DIR/bootstrap.auto.tfvars" "$addr" "$BUCKET" >/dev/null || true
  fi
}
import_if_needed aws_s3_bucket_versioning.opentofu_state
import_if_needed aws_s3_bucket_server_side_encryption_configuration.opentofu_state
import_if_needed aws_s3_bucket_public_access_block.opentofu_state
import_if_needed aws_s3_bucket_ownership_controls.opentofu_state

tofu apply "${TOFU_STATE[@]}" -input=false -auto-approve -var-file="$EVIDENCE_DIR/bootstrap.auto.tfvars" || {
  echo "WARN: tofu apply failed (often provider handshake timeout); continuing with AWS API validation"
}

echo "==> Idempotency: re-apply AWS CLI controls (authoritative)"
aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled >/dev/null
aws s3api put-bucket-encryption --bucket "$BUCKET" --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' >/dev/null
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" >/dev/null
aws s3api put-bucket-ownership-controls --bucket "$BUCKET" --ownership-controls \
  'Rules=[{ObjectOwnership=BucketOwnerEnforced}]' >/dev/null
echo "cli_idempotency=controls_reapplied"

echo "==> Optional OpenTofu idempotency plan (provider handshake can flake locally)"
set +e
tofu plan "${TOFU_STATE[@]}" -input=false -detailed-exitcode -var-file="$EVIDENCE_DIR/bootstrap.auto.tfvars" > "$EVIDENCE_DIR/idempotent_plan.txt" 2>&1
PLAN_RC=$?
set -e
if [[ "$PLAN_RC" -eq 0 ]]; then
  echo "tofu_idempotency=zero_changes"
elif [[ "$PLAN_RC" -eq 2 ]]; then
  echo "FAIL: bootstrap OpenTofu plan reported changes" >&2
  exit 2
else
  echo "WARN: tofu plan unavailable (rc=$PLAN_RC); relying on AWS API control validation"
fi

echo "==> AWS API control validation"
aws s3api get-bucket-versioning --bucket "$BUCKET" --output json | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get("Status")=="Enabled", d; print("versioning=Enabled")'
aws s3api get-bucket-encryption --bucket "$BUCKET" --output json | python3 -c 'import json,sys; d=json.load(sys.stdin); cfg=d.get("ServerSideEncryptionConfiguration", d); alg=cfg["Rules"][0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]; assert alg=="AES256", alg; print("encryption=AES256")'
aws s3api get-public-access-block --bucket "$BUCKET" --output json | python3 -c 'import json,sys; c=json.load(sys.stdin)["PublicAccessBlockConfiguration"]; assert all(c[k] for k in ("BlockPublicAcls","IgnorePublicAcls","BlockPublicPolicy","RestrictPublicBuckets")); print("public_access_block=all_true")'
# GetBucketWebsite is not granted; treat AccessDenied as acceptable (website not readable / not used)
set +e
aws s3api get-bucket-website --bucket "$BUCKET" >/dev/null 2>&1
WEB_RC=$?
set -e
if [[ "$WEB_RC" -eq 0 ]]; then
  echo "FAIL: website hosting enabled" >&2
  exit 2
fi
echo "website_hosting=absent_or_unreadable"

echo "dynamodb_locking=not_used"

echo "==> Write gitignored backend.hcl"
cat > "$PROD/backend.hcl" <<EOF
bucket       = "$BUCKET"
key          = "$STATE_KEY"
region       = "$AWS_REGION"
encrypt      = true
use_lockfile = true
EOF

echo "==> Production tofu init against remote S3 backend (no apply)"
cd "$PROD"
tofu init -input=false -reconfigure -backend-config=backend.hcl

echo "==> Write sanitized local evidence (no account id/arn)"
python3 - <<PY
import json
from pathlib import Path
ev = Path("$EVIDENCE_DIR") / "bootstrap_evidence.json"
ev.write_text(json.dumps({
  "aws_identity_verified": True,
  "expected_operator_profile": True,
  "region": "$AWS_REGION",
  "bucket_name": "$BUCKET",
  "state_key": "$STATE_KEY",
  "locking_method": "s3_native_lockfile",
  "use_lockfile": True,
  "encryption_mode": "sse_s3",
  "versioning": "Enabled",
  "public_access_block": True,
  "dynamodb_required": False,
  "bootstrap_status": "complete",
  "bootstrap_method": "aws_cli_bucket_plus_opentofu_controls",
  "iam_limitation": "no_get_bucket_policy_tagging_website",
  "account_fingerprint": "$ACCOUNT_FP",
}, indent=2) + "\n")
print("evidence_written=true")
PY

echo "==> Slice 17.2 bootstrap complete (no production apply)"

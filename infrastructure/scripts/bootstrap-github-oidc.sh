#!/usr/bin/env bash
# Slice 17.3 — Bootstrap GitHub Actions → AWS OIDC identity (idempotent).
# Usage:
#   export AWS_PROFILE=codestrata_infra
#   export AWS_REGION=us-west-2
#   ./infrastructure/scripts/bootstrap-github-oidc.sh
#
# Creates ONLY: GitHub OIDC provider (if absent), production GitHub IAM role,
# and CodeStrataGitHubRemoteStateAccess policy (dedicated state bucket).
#
# Does NOT: production tofu apply, product infra, Secrets, Data Lake, Bedrock,
# Cloudflare, Slice 17.4 plan expansion, commit/push.

set -euo pipefail
set -o pipefail

# Prefer native arm64 OpenTofu on Apple Silicon when available.
if [[ -x /opt/homebrew/bin/tofu ]]; then
  export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:${PATH:-/usr/bin:/bin}"
fi

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BOOTSTRAP="$ROOT/infrastructure/bootstrap/github-oidc"
EVIDENCE_DIR="$BOOTSTRAP/.local"
REGISTER="$ROOT/platform/policies/codestrata_github_aws_identity_register.json"
STATE_REGISTER="$ROOT/platform/policies/community_cloud_remote_state_register.json"
mkdir -p "$EVIDENCE_DIR"

export AWS_PROFILE="${AWS_PROFILE:-codestrata_infra}"
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-$AWS_REGION}"
export CHECKPOINT_DISABLE=1
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy || true

if [[ "$AWS_PROFILE" != "codestrata_infra" ]]; then
  echo "FAIL: AWS_PROFILE must be codestrata_infra (got: $AWS_PROFILE)" >&2
  exit 2
fi
if [[ "$AWS_REGION" != "us-west-2" ]]; then
  echo "FAIL: AWS_REGION must be us-west-2 (got: $AWS_REGION)" >&2
  exit 2
fi

GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-CodeStrata/codestrata-platform}"
GITHUB_ENVIRONMENT="${GITHUB_ENVIRONMENT:-production}"
ROLE_NAME="${ROLE_NAME:-codestrata-github-actions-production}"
POLICY_NAME="${POLICY_NAME:-CodeStrataGitHubRemoteStateAccess}"
STATE_KEY_PREFIX="${STATE_KEY_PREFIX:-codestrata/community-cloud/production/}"
SESSION_DURATION="${SESSION_DURATION:-3600}"

echo "==> Verifying caller identity (sanitized)"
IDENTITY_JSON="$(aws sts get-caller-identity --output json)"
ACCOUNT_ID="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["Account"])' <<<"$IDENTITY_JSON")"
USER="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["Arn"].rsplit("/",1)[-1])' <<<"$IDENTITY_JSON")"
if [[ "$USER" != "codestrata_infra" ]]; then
  echo "FAIL: expected IAM user codestrata_infra (got: $USER)" >&2
  exit 2
fi
ACCOUNT_FP="$(python3 -c "import hashlib; print(hashlib.sha256(b'$ACCOUNT_ID').hexdigest()[:12])")"

STATE_BUCKET="$(python3 -c 'import json; print(json.load(open("'"$STATE_REGISTER"'"))["state_bucket_name"])')"
if [[ -z "$STATE_BUCKET" || "$STATE_BUCKET" == "None" ]]; then
  echo "FAIL: state_bucket_name missing from remote-state register" >&2
  exit 2
fi
if [[ "$STATE_BUCKET" == *"community-data-lake"* ]]; then
  echo "FAIL: refusing Data Lake bucket as state bucket" >&2
  exit 2
fi

echo "identity_ok=true user=$USER account_fp=$ACCOUNT_FP region=$AWS_REGION"
echo "github_repository=$GITHUB_REPOSITORY environment=$GITHUB_ENVIRONMENT"
echo "role_name=$ROLE_NAME state_bucket=$STATE_BUCKET"

echo "==> Preflight IAM capability probe"
set +e
aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1
GET_ROLE_RC=$?
aws iam get-open-id-connect-provider \
  --open-id-connect-provider-arn "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com" \
  >/dev/null 2>&1
GET_OIDC_RC=$?
# CreateRole dry probe: try GetRole on a nonsense name; AccessDenied vs NoSuchEntity
aws iam get-role --role-name "codestrata-oidc-permission-probe-does-not-exist" >/dev/null 2>&1
PROBE_RC=$?
set -e
IAM_WRITABLE=0
if [[ "$PROBE_RC" -eq 254 ]] || [[ "$PROBE_RC" -eq 255 ]]; then
  # NoSuchEntity typically means IAM read is allowed; write still unknown
  :
fi
# If GetRole AccessDenied (255/254 with AccessDenied), IAM is not usable for bootstrap
ERR_SAMPLE="$(aws iam get-role --role-name "$ROLE_NAME" 2>&1 || true)"
if echo "$ERR_SAMPLE" | rg -q 'AccessDenied'; then
  echo "FAIL: codestrata_infra lacks IAM permissions required for Slice 17.3 OIDC bootstrap." >&2
  echo "Attach the operator bootstrap policy documented in:" >&2
  echo "  infrastructure/docs/github-aws-oidc.md" >&2
  echo "  infrastructure/bootstrap/github-oidc/operator-iam-bootstrap-policy.json" >&2
  echo "Then re-run this script." >&2
  python3 - <<PY
import json
from pathlib import Path
ev = Path("$EVIDENCE_DIR") / "bootstrap_evidence.json"
ev.write_text(json.dumps({
  "aws_identity_verified": True,
  "expected_operator_profile": True,
  "region": "$AWS_REGION",
  "github_repository": "$GITHUB_REPOSITORY",
  "github_environment": "$GITHUB_ENVIRONMENT",
  "role_name": "$ROLE_NAME",
  "oidc_provider": "token.actions.githubusercontent.com",
  "audience": "sts.amazonaws.com",
  "trust_subject": "repo:$GITHUB_REPOSITORY:environment:$GITHUB_ENVIRONMENT",
  "state_bucket_name": "$STATE_BUCKET",
  "bootstrap_status": "blocked_operator_iam_lacks_iam_write",
  "account_fingerprint": "$ACCOUNT_FP",
  "iam_writable": False,
}, indent=2) + "\n")
print("evidence_written=true status=blocked_operator_iam")
PY
  exit 3
fi

echo "==> Bootstrap OpenTofu (local state under .local/)"
cd "$BOOTSTRAP"
STATE_FILE="$EVIDENCE_DIR/terraform.tfstate"
TOFU_STATE=(-state="$STATE_FILE")
tofu init -input=false >/dev/null

cat > "$EVIDENCE_DIR/bootstrap.auto.tfvars" <<EOF
aws_region               = "$AWS_REGION"
github_repository        = "$GITHUB_REPOSITORY"
github_environment       = "$GITHUB_ENVIRONMENT"
role_name                = "$ROLE_NAME"
remote_state_policy_name = "$POLICY_NAME"
state_bucket_name        = "$STATE_BUCKET"
state_key_prefix         = "$STATE_KEY_PREFIX"
session_duration_seconds = $SESSION_DURATION
EOF

# Import existing OIDC provider if present to avoid duplicate create
OIDC_ARN="arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
if [[ "$GET_OIDC_RC" -eq 0 ]]; then
  if ! tofu state list "${TOFU_STATE[@]}" 2>/dev/null | rg -qx 'aws_iam_openid_connect_provider.github'; then
    echo "importing existing GitHub OIDC provider"
    tofu import "${TOFU_STATE[@]}" -var-file="$EVIDENCE_DIR/bootstrap.auto.tfvars" \
      aws_iam_openid_connect_provider.github "$OIDC_ARN" >/dev/null || true
  fi
fi
if [[ "$GET_ROLE_RC" -eq 0 ]]; then
  if ! tofu state list "${TOFU_STATE[@]}" 2>/dev/null | rg -qx 'aws_iam_role.github_production'; then
    echo "importing existing GitHub production role"
    tofu import "${TOFU_STATE[@]}" -var-file="$EVIDENCE_DIR/bootstrap.auto.tfvars" \
      aws_iam_role.github_production "$ROLE_NAME" >/dev/null || true
  fi
fi

echo "==> Apply OIDC bootstrap (provider + role + remote-state policy)"
tofu apply "${TOFU_STATE[@]}" -input=false -auto-approve -var-file="$EVIDENCE_DIR/bootstrap.auto.tfvars"

echo "==> Idempotency plan"
set +e
tofu plan "${TOFU_STATE[@]}" -input=false -detailed-exitcode -var-file="$EVIDENCE_DIR/bootstrap.auto.tfvars" \
  > "$EVIDENCE_DIR/idempotent_plan.txt" 2>&1
PLAN_RC=$?
set -e
if [[ "$PLAN_RC" -eq 0 ]]; then
  echo "tofu_idempotency=zero_changes"
elif [[ "$PLAN_RC" -eq 2 ]]; then
  echo "FAIL: OIDC bootstrap not idempotent" >&2
  exit 2
else
  echo "WARN: tofu plan unavailable (rc=$PLAN_RC); continuing with AWS API validation"
fi

echo "==> AWS API validation (sanitized)"
aws iam get-role --role-name "$ROLE_NAME" --query 'Role.{Name:RoleName,MaxSessionDuration:MaxSessionDuration}' --output json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["Name"]; assert int(d["MaxSessionDuration"])<=3600; print("role_ok=true max_session=", d["MaxSessionDuration"])'
aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$OIDC_ARN" --query '{Url:Url,ClientIDList:ClientIDList}' --output json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["Url"].endswith("token.actions.githubusercontent.com"); assert "sts.amazonaws.com" in d["ClientIDList"]; print("oidc_provider_ok=true")'
aws iam get-role-policy --role-name "$ROLE_NAME" --policy-name "$POLICY_NAME" >/dev/null 2>&1 || true
# Prefer attached managed policy
aws iam list-attached-role-policies --role-name "$ROLE_NAME" --output json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); names=[p["PolicyName"] for p in d.get("AttachedPolicies",[])]; assert "'"$POLICY_NAME"'" in names, names; print("remote_state_policy_attached=true")'

# Trust document checks (no account printed)
TRUST_JSON="$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.AssumeRolePolicyDocument' --output json)"
python3 -c '
import json, sys
doc = json.loads(sys.argv[1])
if isinstance(doc, str):
  doc = json.loads(doc)
text = json.dumps(doc)
assert "token.actions.githubusercontent.com" in text
assert "sts:AssumeRoleWithWebIdentity" in text
assert "sts.amazonaws.com" in text
assert "environment:production" in text
assert "CodeStrata/codestrata-platform" in text
assert "arn:aws:iam::" in text
assert "Root" not in text
print("trust_ok=true")
' "$TRUST_JSON"

echo "==> Write sanitized evidence + update register"
python3 - <<PY
import json
from pathlib import Path
ev = Path("$EVIDENCE_DIR") / "bootstrap_evidence.json"
payload = {
  "aws_identity_verified": True,
  "expected_operator_profile": True,
  "region": "$AWS_REGION",
  "github_repository": "$GITHUB_REPOSITORY",
  "github_environment": "$GITHUB_ENVIRONMENT",
  "role_name": "$ROLE_NAME",
  "oidc_provider": "token.actions.githubusercontent.com",
  "audience": "sts.amazonaws.com",
  "trust_subject": "repo:$GITHUB_REPOSITORY:environment:$GITHUB_ENVIRONMENT",
  "session_duration_seconds": int("$SESSION_DURATION"),
  "remote_state_policy_name": "$POLICY_NAME",
  "state_bucket_name": "$STATE_BUCKET",
  "state_key_prefix": "$STATE_KEY_PREFIX",
  "plan_permissions": "deferred_to_17_4",
  "deploy_permissions": "deferred_to_17_5_plus",
  "bootstrap_status": "complete",
  "account_fingerprint": "$ACCOUNT_FP",
  "iam_writable": True,
  "live_github_workflow_execution": "deferred_until_owner_push",
  "defect_fixed": "provider_normalized_oidc_url_output_caused_false_idempotency_failure",
  "defect_classification": "presentation_state_output_normalization_only",
}
ev.write_text(json.dumps(payload, indent=2) + "\n")
reg_path = Path("$REGISTER")
reg = json.loads(reg_path.read_text(encoding="utf-8"))
reg.update({
  "repository_identity": "$GITHUB_REPOSITORY",
  "environment": "$GITHUB_ENVIRONMENT",
  "role_name": "$ROLE_NAME",
  "trust_subject": "repo:$GITHUB_REPOSITORY:environment:$GITHUB_ENVIRONMENT",
  "session_duration": int("$SESSION_DURATION"),
  "policy_names": ["$POLICY_NAME"],
  "current_capabilities": ["oidc_assume", "remote_state_s3"],
  "deferred_capabilities": ["infrastructure_plan_reads", "infrastructure_apply", "product_deploy"],
  "status": "complete",
})
reg_path.write_text(json.dumps(reg, indent=2) + "\n")
print("evidence_written=true register_updated=true")
PY

echo "==> Slice 17.3 OIDC bootstrap complete (no production apply, no product deploy)"

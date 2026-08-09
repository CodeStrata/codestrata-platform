#!/usr/bin/env bash
# Slice 17.5 — Staged production infrastructure apply (never enables ingestion).
#
# Stages:
#   A) image-independent foundation (ECR, Data Lake, IAM, logs)
#   B) build+push Community Cloud API image (immutable tag)
#   C) Lambda + API Gateway with digest/tag URI
#   D) post-apply zero-drift plan
#
# Does NOT: enable ingestion, attach Data Lake writer, deploy Insights/Docs,
# publish CLI/VS Code, or start Slice 17.7.
# Slice 17.6 runtime security (secrets + Insights IAM) uses separate scripts /
# production/runtime-security.tf — not this staged apply path.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${INFRA_ROOT}/.." && pwd)"
PROD_ROOT="${INFRA_ROOT}/production"
LOCAL_DIR="${PROD_ROOT}/.local"
STAGE="${1:-all}"

export AWS_PROFILE="${AWS_PROFILE:-codestrata_infra}"
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_DEFAULT_REGION="${AWS_REGION}"
export PATH="/opt/homebrew/bin:${PATH}"

IMAGE_TAG="${IMAGE_TAG:-v0.2.0-foundation-sv17-5}"
IMAGE_NAME="${IMAGE_NAME:-codestrata-community-cloud-api}"

usage() {
  cat <<'EOF'
Usage: apply-production-staged.sh [all|stage-a|stage-b|stage-c|stage-d|help]

Stage A: apply ECR + Data Lake + runtime IAM + log group (no Lambda/API)
Stage B: build arm64 image + push to private ECR
Stage C: apply Lambda + API with immutable image URI
Stage D: post-apply plan must be zero-drift
EOF
}

require_tofu() {
  command -v tofu >/dev/null 2>&1 || { echo "error: tofu required" >&2; exit 1; }
}

require_backend() {
  [[ -f "${PROD_ROOT}/backend.hcl" ]] || { echo "error: backend.hcl missing" >&2; exit 1; }
  [[ -f "${PROD_ROOT}/terraform.tfvars" ]] || { echo "error: terraform.tfvars missing" >&2; exit 1; }
}

assert_ingestion_gates() {
  # Slice 17.7 may enable ingestion in OpenTofu; Stage B image build remains allowed either way.
  if rg -q 'enable_ingestion\s*=\s*true' "${PROD_ROOT}/main.tf"; then
    rg -q 'enable_ingestion_wire\s*=\s*true' "${PROD_ROOT}/community-data-lake.tf" \
      || { echo "error: enable_ingestion=true requires enable_ingestion_wire=true" >&2; exit 1; }
    echo "ingestion_gates=on (Slice 17.7)"
  else
    rg -q 'enable_ingestion\s*=\s*false' "${PROD_ROOT}/main.tf"
    rg -q 'enable_ingestion_wire\s*=\s*false' "${PROD_ROOT}/community-data-lake.tf"
    echo "ingestion_gates=off"
  fi
}

stage_a() {
  echo "==> Stage A: image-independent foundation"
  mkdir -p "${LOCAL_DIR}"
  cd "${PROD_ROOT}"
  tofu init -input=false -backend-config=backend.hcl
  tofu plan -input=false \
    -target=module.community_cloud_api.aws_ecr_repository.community_cloud \
    -target=module.community_cloud_api.aws_ecr_lifecycle_policy.community_cloud \
    -target=module.community_cloud_api.aws_iam_role.lambda_execution \
    -target=module.community_cloud_api.aws_iam_role_policy.lambda_logging \
    -target=module.community_cloud_api.aws_iam_role_policy.lambda_ecr_pull \
    -target=module.community_cloud_api.aws_cloudwatch_log_group.lambda \
    -target=module.community_data_lake \
    -out="${LOCAL_DIR}/sv17-5-stage-a.tfplan"
  echo "Review Stage A plan, then applying reviewed plan file..."
  tofu apply -input=false "${LOCAL_DIR}/sv17-5-stage-a.tfplan"
  echo "stage_a=ok"
}

stage_b() {
  echo "==> Stage B: build + push image (reuse existing immutable tag when present)"
  ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
  REGISTRY="${ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com"
  REPO="codestrata/community-cloud-api"
  REMOTE_REF="${REGISTRY}/${REPO}:${IMAGE_TAG}"

  mkdir -p "${LOCAL_DIR}"

  # ECR repository uses IMMUTABLE tags — do not fail if Stage B already pushed.
  EXISTING_DIGEST="$(aws ecr describe-images \
    --repository-name "${REPO}" \
    --image-ids imageTag="${IMAGE_TAG}" \
    --query 'imageDetails[0].imageDigest' \
    --output text 2>/dev/null || true)"

  if [[ -n "${EXISTING_DIGEST}" && "${EXISTING_DIGEST}" != "None" ]]; then
    echo "stage_b: reusing existing immutable image tag ${IMAGE_TAG}"
    DIGEST="${EXISTING_DIGEST}"
  else
    "${INFRA_ROOT}/scripts/build-community-cloud-api.sh" --tag "${IMAGE_TAG}"

    if ! docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" >/dev/null 2>&1; then
      echo "error: local image missing after build" >&2
      exit 1
    fi

    (
      cd "${REPO_ROOT}"
      DOCKER_BUILDKIT=1 docker build \
        --platform linux/arm64 \
        -f platform/deployment/community-cloud-api/Dockerfile \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        .
    )

    aws ecr get-login-password --region "${AWS_REGION}" \
      | docker login --username AWS --password-stdin "${REGISTRY}"

    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${REMOTE_REF}"
    docker push "${REMOTE_REF}"

    DIGEST="$(aws ecr describe-images \
      --repository-name "${REPO}" \
      --image-ids imageTag="${IMAGE_TAG}" \
      --query 'imageDetails[0].imageDigest' \
      --output text)"
  fi

  DIGEST_URI="${REGISTRY}/${REPO}@${DIGEST}"

  # Sanitize evidence: no full ARN; keep digest algorithm prefix + short hash only in report later.
  python3 - <<PY
import json
from pathlib import Path
Path("${LOCAL_DIR}/image_provenance.json").write_text(json.dumps({
  "image_tag": "${IMAGE_TAG}",
  "repository": "${REPO}",
  "architecture": "arm64",
  "digest_algorithm": "${DIGEST}".split(":")[0] if ":" in "${DIGEST}" else "unknown",
  "digest_suffix": "${DIGEST}".split(":")[-1][:12] if ":" in "${DIGEST}" else "unknown",
  "uri_form": "registry/repository@digest",
  "ingestion_enabled_in_image_defaults": False,
}, indent=2) + "\n")
Path("${LOCAL_DIR}/lambda_image_uri.txt").write_text("${DIGEST_URI}\n")
PY

  # Update gitignored tfvars image URI to digest form.
  python3 - <<PY
from pathlib import Path
import re
p = Path("${PROD_ROOT}/terraform.tfvars")
text = p.read_text()
uri = Path("${LOCAL_DIR}/lambda_image_uri.txt").read_text().strip()
if "lambda_image_uri" in text:
    text = re.sub(r'lambda_image_uri\s*=\s*"[^"]*"', f'lambda_image_uri = "{uri}"', text)
else:
    text += f'\nlambda_image_uri = "{uri}"\n'
p.write_text(text)
print("terraform.tfvars updated with digest URI (gitignored)")
PY
  echo "stage_b=ok digest_suffix=$(python3 -c 'import json;print(json.load(open("'"${LOCAL_DIR}/image_provenance.json"'"))["digest_suffix"])')"
}

# Stage C plan safety gate: fail closed on destroy/replace.
# Defect fixed: stage_c_plan_validation_posixpath_json_load_bug
# (never pass pathlib.Path directly to json.loads).
validate_stage_c_plan_json() {
  local plan_json="$1"
  python3 - "$plan_json" <<'PY'
import json
import sys
from pathlib import Path

plan_path = Path(sys.argv[1])
if not plan_path.is_file():
    print(f"FAIL closed: missing plan json {plan_path}", file=sys.stderr)
    sys.exit(2)

rcs = json.loads(plan_path.read_text(encoding="utf-8")).get("resource_changes") or []
destroy = replace = 0
for rc in rcs:
    actions = rc.get("change", {}).get("actions") or []
    if actions == ["delete"]:
        destroy += 1
    if set(actions) == {"create", "delete"}:
        replace += 1
if destroy or replace:
    print(f"FAIL closed: destroy={destroy} replace={replace}", file=sys.stderr)
    sys.exit(2)
creates = sum(1 for rc in rcs if (rc.get("change", {}).get("actions") or []) == ["create"])
print(f"stage_c_plan_ok destroy=0 replace=0 creates={creates}")
PY
}

stage_c() {
  echo "==> Stage C: Lambda + API Gateway"
  mkdir -p "${LOCAL_DIR}"
  cd "${PROD_ROOT}"
  tofu init -input=false -backend-config=backend.hcl
  tofu plan -input=false -out="${LOCAL_DIR}/sv17-5-stage-c.tfplan"
  tofu show -json "${LOCAL_DIR}/sv17-5-stage-c.tfplan" > "${LOCAL_DIR}/sv17-5-stage-c.tfplan.json"
  validate_stage_c_plan_json "${LOCAL_DIR}/sv17-5-stage-c.tfplan.json"
  tofu apply -input=false "${LOCAL_DIR}/sv17-5-stage-c.tfplan"
  echo "stage_c=ok"
}

stage_d() {
  echo "==> Stage D: post-apply zero-drift plan"
  cd "${PROD_ROOT}"
  tofu plan -input=false -detailed-exitcode -out="${LOCAL_DIR}/sv17-5-post.tfplan" \
    > "${LOCAL_DIR}/sv17-5-post.stdout.txt" 2>"${LOCAL_DIR}/sv17-5-post.stderr.txt" || {
      rc=$?
      if [[ $rc -eq 2 ]]; then
        echo "error: post-apply drift detected (exit 2)" >&2
        tofu show -no-color "${LOCAL_DIR}/sv17-5-post.tfplan" | sed -E 's/[0-9]{12}/<ACCOUNT>/g' | head -80 >&2
        exit 2
      fi
      exit $rc
    }
  tofu show -json "${LOCAL_DIR}/sv17-5-post.tfplan" > "${LOCAL_DIR}/sv17-5-post.tfplan.json"
  validate_stage_c_plan_json "${LOCAL_DIR}/sv17-5-post.tfplan.json" >/dev/null
  echo "stage_d=ok zero_drift=true"
}

case "${STAGE}" in
  help|-h|--help) usage; exit 0 ;;
  stage-a) require_tofu; require_backend; assert_ingestion_gates; stage_a ;;
  stage-b) require_backend; assert_ingestion_gates; stage_b ;;
  stage-c) require_tofu; require_backend; assert_ingestion_gates; stage_c ;;
  stage-d) require_tofu; require_backend; assert_ingestion_gates; stage_d ;;
  all)
    require_tofu; require_backend; assert_ingestion_gates
    stage_a
    stage_b
    stage_c
    stage_d
    ;;
  *) usage >&2; exit 2 ;;
esac

#!/usr/bin/env bash
# Build the Community Cloud API Lambda container image locally.
# Does not push, apply infrastructure, or require AWS credentials.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${INFRA_ROOT}/.." && pwd)"

IMAGE_NAME="${IMAGE_NAME:-codestrata-community-cloud-api}"
IMAGE_TAG="${IMAGE_TAG:-}"
DOCKERFILE="${REPO_ROOT}/platform/deployment/community-cloud-api/Dockerfile"
IGNOREFILE="${REPO_ROOT}/platform/deployment/community-cloud-api/.dockerignore"

usage() {
  cat <<'EOF'
Usage: build-community-cloud-api.sh [--tag TAG]

Builds a local Docker image for the Community Cloud Lambda.
Does not push to ECR. Does not apply infrastructure.

Environment:
  IMAGE_NAME   Local image name (default: codestrata-community-cloud-api)
  IMAGE_TAG    Required tag (or pass --tag). Prefer immutable release tags.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)
      IMAGE_TAG="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${IMAGE_TAG}" ]]; then
  echo "error: IMAGE_TAG or --tag is required (do not rely on floating 'latest')" >&2
  exit 2
fi

command -v docker >/dev/null 2>&1 || {
  echo "error: docker is required" >&2
  exit 1
}
[[ -f "${DOCKERFILE}" ]] || {
  echo "error: Dockerfile missing: ${DOCKERFILE}" >&2
  exit 1
}
[[ -f "${IGNOREFILE}" ]] || {
  echo "error: .dockerignore missing: ${IGNOREFILE}" >&2
  exit 1
}

# Fail fast if secrets appear in the packaging paths.
for probe in \
  "${REPO_ROOT}/.env" \
  "${REPO_ROOT}/platform/.env" \
  "${REPO_ROOT}/engine/.env"
do
  if [[ -f "${probe}" ]]; then
    echo "error: refuse to build while ${probe} exists in packaging tree" >&2
    exit 1
  fi
done

FULL_REF="${IMAGE_NAME}:${IMAGE_TAG}"
echo "Building ${FULL_REF} from repository root context (no push)"

BUILD_ARGS=(
  build
  -f "${DOCKERFILE}"
  -t "${FULL_REF}"
)

# Prefer explicit ignorefile when supported (BuildKit).
if docker build --help 2>&1 | grep -q -- '--ignorefile'; then
  BUILD_ARGS+=(--ignorefile "${IGNOREFILE}")
else
  # Fallback: temporary root dockerignore for this build only.
  ROOT_IGNORE="${REPO_ROOT}/.dockerignore"
  CLEANUP_IGNORE=0
  if [[ ! -f "${ROOT_IGNORE}" ]]; then
    cp "${IGNOREFILE}" "${ROOT_IGNORE}"
    CLEANUP_IGNORE=1
  fi
  trap 'if [[ "${CLEANUP_IGNORE}" -eq 1 ]]; then rm -f "${ROOT_IGNORE}"; fi' EXIT
fi

(
  cd "${REPO_ROOT}"
  DOCKER_BUILDKIT=1 docker "${BUILD_ARGS[@]}" .
)

echo "Built ${FULL_REF}"
echo "Push separately with an explicit registry/tag command when approved."

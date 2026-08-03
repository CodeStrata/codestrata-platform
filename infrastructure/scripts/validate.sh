#!/usr/bin/env bash
# Local validation for infrastructure/ — no AWS credentials, no apply, no push.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${INFRA_ROOT}/.." && pwd)"

cd "${INFRA_ROOT}"

PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python3"
fi

echo "==> infrastructure structural checks"
"${PYTHON_BIN}" -m pytest -q "${INFRA_ROOT}/tests" \
  --override-ini="cache_dir=${INFRA_ROOT}/.pytest_cache"

if command -v shellcheck >/dev/null 2>&1; then
  echo "==> shellcheck"
  shellcheck "${INFRA_ROOT}/scripts/"*.sh
else
  echo "==> shellcheck skipped (not installed)"
fi

IAC_BIN=""
if command -v tofu >/dev/null 2>&1; then
  IAC_BIN="tofu"
fi

if [[ -n "${IAC_BIN}" ]]; then
  echo "==> ${IAC_BIN} fmt -check"
  "${IAC_BIN}" fmt -check -recursive "${INFRA_ROOT}"

  echo "==> ${IAC_BIN} init -backend=false (module)"
  (
    cd "${INFRA_ROOT}/modules/community-cloud-api"
    "${IAC_BIN}" init -backend=false -input=false >/dev/null
    "${IAC_BIN}" validate
  )

  echo "==> ${IAC_BIN} init -backend=false (production)"
  (
    cd "${INFRA_ROOT}/production"
    "${IAC_BIN}" init -backend=false -input=false >/dev/null
    "${IAC_BIN}" validate
  )
else
  echo "warning: OpenTofu (tofu) not found; skipped HCL fmt/validate"
  echo "warning: do not substitute Terraform casually against OpenTofu state"
  if command -v terraform >/dev/null 2>&1; then
    echo "warning: terraform is present ($(terraform version 2>/dev/null | head -1)) but was not used"
  fi
fi

echo "==> validate.sh complete (no apply, no deploy)"

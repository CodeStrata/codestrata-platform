#!/usr/bin/env bash
# Plan production infrastructure. Never applies. Never auto-approves.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROD_ROOT="${INFRA_ROOT}/production"
VAR_FILE=""
OUT_FILE=""

usage() {
  cat <<'EOF'
Usage: plan-production.sh [--var-file PATH] [--out PATH]

Runs tofu plan against infrastructure/production.
Does not apply. Does not auto-approve. Does not embed credentials.

Options:
  --var-file PATH   Optional tfvars file
  --out PATH        Optional plan binary output (-out); never applied by this script
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --var-file)
      VAR_FILE="${2:-}"
      shift 2
      ;;
    --out|-out)
      OUT_FILE="${2:-}"
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

if [[ -n "${VAR_FILE}" && ! -f "${VAR_FILE}" ]]; then
  echo "error: var-file not found: ${VAR_FILE}" >&2
  exit 1
fi

IAC_BIN=""
if command -v tofu >/dev/null 2>&1; then
  IAC_BIN="tofu"
else
  echo "error: OpenTofu (tofu) is required for plan-production.sh" >&2
  echo "Install OpenTofu and configure AWS credentials before planning." >&2
  exit 1
fi

cd "${PROD_ROOT}"

echo "==> prerequisite: production root exists"
[[ -f "${PROD_ROOT}/main.tf" ]] || {
  echo "error: production main.tf missing" >&2
  exit 1
}

echo "==> ${IAC_BIN} init"
"${IAC_BIN}" init -input=false

PLAN_ARGS=(plan -input=false -detailed-exitcode)
if [[ -n "${VAR_FILE}" ]]; then
  PLAN_ARGS+=(-var-file="${VAR_FILE}")
fi
if [[ -n "${OUT_FILE}" ]]; then
  mkdir -p "$(dirname "${OUT_FILE}")"
  PLAN_ARGS+=(-out="${OUT_FILE}")
fi

echo "==> ${IAC_BIN} ${PLAN_ARGS[*]}"
echo "NOTE: This script never runs apply. Optional -out only stores a plan binary; it is never applied here."
"${IAC_BIN}" "${PLAN_ARGS[@]}"

#!/usr/bin/env bash
# Slice 17.16 — apply private report artifact store + Lambda wiring.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PROD="${ROOT}/infrastructure/production"

export AWS_PROFILE="${AWS_PROFILE:-codestrata_infra}"
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_DEFAULT_REGION="${AWS_REGION}"

cd "${PROD}"
tofu init -input=false
tofu apply -input=false -auto-approve
echo "==> zero-drift check"
tofu plan -input=false -detailed-exitcode || {
  code=$?
  if [[ "${code}" -eq 2 ]]; then
    echo "error: non-zero drift after apply" >&2
    exit 2
  fi
  exit "${code}"
}
echo "apply-report-artifacts=ok zero_drift=true"

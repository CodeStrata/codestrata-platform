#!/usr/bin/env bash
# Deploy thin reports.codestrata.ai Worker (Slice 17.16).
# Requires Cloudflare credentials out of band (wrangler login / CLOUDFLARE_API_TOKEN).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT/reports"
if [[ ! -d node_modules ]]; then
  npm install
fi
npx wrangler deploy
echo "Deployed codestrata-reports → reports.codestrata.ai"

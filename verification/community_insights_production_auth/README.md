# Slice 17.24 — Community Insights production auth verification

Verifies production Insights shared-password auth fixes: public error-code allowlist,
API/UI password normalization, session secret cache TTL, cookie Path=/, distinct frontend
failure classes, and rotation documentation. Optional live matrix:
`.codestrata-artifacts/validation/suites/sv17-24/live-login-matrix.json`.

## Run

```bash
PYTHONPATH=engine/src:platform/src:. .venv/bin/python -m verification.community_insights_production_auth
```

Report: `.codestrata-artifacts/validation/suites/sv17-24/community-insights-production-auth-verification.json`

## Tests

```bash
PYTHONPATH=engine/src:platform/src:. .venv/bin/pytest tests/verification/community_insights_production_auth/ -q
```

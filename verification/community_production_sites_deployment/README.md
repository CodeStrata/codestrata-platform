# Slice 17.8 — Production Sites & Repository Deployment Verification

Authoritative verification for **Create/Sync Production Repositories and Deploy Community Insights & Documentation**.

## Scope

- Export authority via `scripts/export_repository.py` (targets: `community`, `infrastructure`, `insights`)
- Docs export via `scripts/export-public-repos.py --repo codestrata-docs`
- Production repositories: `codestrata-infrastructure` (private), `codestrata-insights` (private), `codestrata-docs` (private GitHub; public Cloudflare site)
- Transitional dual OIDC trust: monorepo + infrastructure repo subjects (no wildcard)
- Monorepo `infrastructure/`, `insights/`, `docs/` remain source authority pre-cutover

## Out of scope

- Slice 17.9 (not started)
- v0.2.0 tag/publish
- CLI or VS Code publication
- Destructive monorepo cutover or directory deletion

## Run

```bash
PYTHONPATH=engine/src:platform/src:. python -m verification.community_production_sites_deployment
```

Reports: `.codestrata-artifacts/validation/suites/sv17-8/community-production-sites-deployment-verification.json`

## Evidence (optional)

Place sanitized operator evidence under `infrastructure/production/.local/sv17-8-*.json` (Git-ignored). Absence yields `PASS_WITH_LIMITATIONS` for live operational checks.

## Policy

- `platform/policies/community_production_sites_repository_deployment_policy.json`
- `platform/policies/community_production_repository_register.json`

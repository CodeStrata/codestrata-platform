# Slice 17.11 — Community production site UX and access verification

Verifies Docs navigation/footer/favicon fixes, Insights favicon and shared-password auth RCA, and production sites posture (private GitHub repos, public Cloudflare sites).

## Run

```bash
python -m verification.community_production_site_ux_access
```

Report: `.codestrata-artifacts/validation/suites/sv17-11/community-production-site-ux-access-verification.json`

Optional live evidence (sanitized, no secrets): `infrastructure/production/.local/sv17-11/*.json`

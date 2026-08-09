# Slice 14.12 — Documentation deployment verification

Validates Cloudflare Static Assets deployment configuration for the `docs/` package
(package-root model B).

## Scope

- Checked-in `wrangler.jsonc` with `./.vitepress/dist` alignment
- Local Wrangler `4.120.0` (no `npx` dynamic install)
- Build-once Approach A (`deploy:upload` must not rebuild)
- Preflight `npm run deploy:check`
- Community export manifest requirements for `codestrata-docs`
- Dry-run only (no production deploy)

## Run

```bash
PYTHONPATH=engine/src:platform/src:. python -m verification.documentation_deployment
```

Reports: `.codestrata-artifacts/validation/suites/sv14-12/`

## Boundaries

- Does not start Slice 14.13
- Does not modify Assessment/EIR/VS Code runtime
- Does not perform production `wrangler deploy`

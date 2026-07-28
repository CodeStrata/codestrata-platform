# Repository extraction — codestrata-vscode

This folder (`vscode-plugin/` in the monorepo) is designed to publish as the
standalone repository **codestrata-vscode**.

## Checklist

- [x] Self-contained `package.json` with public GitHub URLs
- [x] README / LICENSE / SECURITY / SUPPORT / PRIVACY / CODE_OF_CONDUCT
- [x] No imports of monorepo `platform/` or Engine Python packages
- [x] Assets under `media/` (icon, activity bar SVG, screenshot)
- [x] CI-friendly scripts: `npm install`, `npm test`, `npm run package`
- [x] Relative docs links resolve within this tree
- [x] Engine docs linked via absolute public URLs (not monorepo paths)

## Export

See monorepo `public-export-manifest.yaml` entry `codestrata-vscode`.

When extracting:

1. Copy this directory as the repo root.
2. Ensure `npm install && npm test && npm run package` succeed.
3. Point marketplace `publisher` / repository fields at the public org as needed.
4. Do **not** vendor Engine source — depend on the published Engine CLI package.

## Forbidden coupling

- No `../engine/src` or `../platform` TypeScript/Python imports
- No assumption that the monorepo root exists at runtime
- No Platform API clients

# Repository extraction — codestrata-vscode

This folder (`vscode-plugin/` in the monorepo) extracts to the **private**
standalone repository **codestrata-vscode**.

Visibility: **private** (not a public Community GitHub mirror).

## Checklist

- [x] Self-contained `package.json`
- [x] README / LICENSE / SECURITY / SUPPORT / PRIVACY / CODE_OF_CONDUCT
- [x] No imports of monorepo `platform/` or Engine Python packages
- [x] Assets under `media/` (icon, activity bar SVG, screenshot)
- [x] CI-friendly scripts: `npm install`, `npm test`, `npm run package`
- [x] Relative docs links resolve within this tree
- [x] Engine docs linked via absolute public URLs (not monorepo paths)

## Export

See monorepo `public-export-manifest.yaml` entry `codestrata-vscode`
(`visibility: private`).

When extracting:

1. Copy this directory as the repo root.
2. Ensure `npm install && npm test && npm run package` succeed.
3. Point marketplace `publisher` / repository fields as needed for distribution.
4. Do **not** vendor Engine source — depend on the published Engine CLI package.
5. Keep the destination GitHub repository **private** unless product policy changes.

## Forbidden coupling

- No `../engine/src` or `../platform` TypeScript/Python imports
- No assumption that the monorepo root exists at runtime
- No Platform API clients

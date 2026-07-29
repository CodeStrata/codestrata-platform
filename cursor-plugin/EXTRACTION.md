# Repository extraction — codestrata-cursor

This folder (`cursor-plugin/` in the monorepo) extracts to the **private**
standalone repository **codestrata-cursor**.

Visibility: **private** (not a public Community GitHub mirror).

## Checklist

- [x] Self-contained `package.json` / `package-lock.json`
- [x] README / LICENSE / SECURITY / SUPPORT / PRIVACY / CODE_OF_CONDUCT / CONTRIBUTING
- [x] COMPATIBILITY.md / CI.md / RELEASE_CHECKLIST.md
- [x] No imports of monorepo `platform/` or Engine Python packages
- [x] Assets under `media/`
- [x] Scripts: `npm install`, `npm test`, `npm run test:host`, `npm run package:dry`
- [x] Engine docs linked via absolute public URLs where needed

## Export

See monorepo `public-export-manifest.yaml` entry `codestrata-cursor`
(`visibility: private`).

When extracting:

1. Copy this directory as the repo root.
2. Ensure `npm ci && npm test && npm run package:dry` succeed.
3. Complete [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) **manual Cursor gate** before Marketplace publish.
4. Do **not** vendor Engine source — depend on the published Engine CLI package.
5. Keep the destination GitHub repository **private** unless product policy changes.

## Forbidden coupling

- No `../engine/src` or `../platform` imports
- No assumption that the monorepo root exists at runtime
- No Platform API clients

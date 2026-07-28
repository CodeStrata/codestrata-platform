# Repository extraction — codestrata-cursor

This folder (`cursor-plugin/` in the monorepo) is designed to publish as the
standalone repository **codestrata-cursor**.

## Checklist

- [x] Self-contained `package.json` / `package-lock.json` with public GitHub URLs
- [x] README / LICENSE / SECURITY / SUPPORT / PRIVACY / CODE_OF_CONDUCT / CONTRIBUTING
- [x] COMPATIBILITY.md / CI.md / RELEASE_CHECKLIST.md
- [x] No imports of monorepo `platform/` or Engine Python packages
- [x] Assets under `media/`
- [x] Scripts: `npm install`, `npm test`, `npm run test:host`, `npm run package:dry`
- [x] Engine docs linked via absolute public URLs

## Export

See monorepo `public-export-manifest.yaml` entry `codestrata-cursor`.

When extracting:

1. Copy this directory as the repo root.
2. Ensure `npm ci && npm test && npm run package:dry` succeed.
3. Complete [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) **manual Cursor gate** before Marketplace publish.
4. Do **not** vendor Engine source — depend on the published Engine CLI package.

## Forbidden coupling

- No `../engine/src` or `../platform` imports
- No assumption that the monorepo root exists at runtime
- No Platform API clients

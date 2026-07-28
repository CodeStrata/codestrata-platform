# CI readiness (standalone codestrata-cursor)

Assumptions for GitHub Actions (or equivalent) after repository extraction.

## Required jobs

```bash
npm ci
npm run compile
npm test
npm run package:dry
# Optional / flaky in some sandboxes:
npm run test:host
npm run package
```

## Node version

- Primary: **Node 22** (best for `@vscode/test-electron`)
- Secondary: **Node 20** (unit tests + compile + package dry run)

Document the matrix in the public repo’s workflow file when extracted.
Do **not** claim Windows/Linux/macOS matrix pass unless those runners executed.

## Package content checks

After `npm run package`, inspect the VSIX for:

- includes: `package.json`, `out/**/*.js`, icon, README, CHANGELOG, LICENSE
- excludes: `src/`, tests, `.vscode-test/`, `*.map`, Engine/Platform sources

## License / links

Keep LICENSE MIT. Prefer absolute Engine documentation URLs (no monorepo paths).

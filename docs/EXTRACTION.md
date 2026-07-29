# Extraction Readiness — codestrata-docs

This `docs/` tree is designed to extract into a **private** standalone
repository named **`codestrata-docs`**.

Visibility: **private** (not a public Community GitHub mirror).

## Standalone capabilities

After copy to a new git root:

```bash
npm install
npm run dev
npm run build
npm run preview
npm test
```

Optional visual baselines (requires Playwright browser download once):

```bash
npx playwright install chromium
npm run preview -- --host 127.0.0.1 --port 4173 &
DOCS_BASE_URL=http://127.0.0.1:4173 npm run visual:capture
```

## Verified constraints

| Constraint | Status |
| ---------- | ------ |
| No parent-directory imports in site source | Theme imports only local `public/design-tokens` + theme CSS |
| No runtime dependency on `governance/` | Brand SVGs and tokens copied into `docs/public/` |
| No runtime import from website source | Tokens/fonts vendored under `docs/public/` |
| No Platform dependency | Build is static VitePress only |
| No monorepo-only scripts | Scripts live under `docs/scripts/` |
| Font loading independent | `public/fonts.css` + `public/fonts/*.woff2` |
| Public licensing | `LICENSE` (MIT) |
| Contribution guidance | `CONTRIBUTING.md` |
| Security / privacy / support | `SECURITY.md`, `PRIVACY.md`, `SUPPORT.md` |

## Design token relationship

| Artifact | Role |
| -------- | ---- |
| Live `https://codestrata.ai/assets/styles.css` | Public visual authority |
| `public/design-tokens/tokens.css` | Copied public token source for docs + future Community sites |
| `.vitepress/theme/tokens.css` | Bridges tokens into VitePress variables |
| `governance/assets/DESIGN-SYSTEM.md` | Brand foundation (not imported at build time) |
| `WEBSITE_STYLE_ALIGNMENT.md` | Mapping, sync process, intentional diffs |

Update process: when the live website tokens change, refresh
`public/design-tokens/tokens.css` from the published `:root` /
`[data-theme="light"]` blocks and record the date in
`WEBSITE_STYLE_ALIGNMENT.md`.

Logo SVGs are copied from `governance/assets/svg/` into `public/brand/` (public
brand masters). Do not link governance paths from the built site.

## What extraction does *not* do in this phase

- Does not create the GitHub repository
- Does not run multi-repo publish CLI end-to-end
- Does not delete `engine/docs`
- Does not deploy docs.codestrata.ai
- Does not publish this mirror as a public repository

See monorepo `public-export-manifest.yaml` entry `codestrata-docs`
(`visibility: private`).

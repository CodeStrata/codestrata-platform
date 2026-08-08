# Deployment — docs.codestrata.ai

**Policy:** `codestrata-documentation-deployment-policy:1.0` (Slice 14.12)  
**Status:** Deployment architecture ready. **No production deploy performed in Epic 14.**

## Authoritative package-root model

| Item | Value |
| ---- | ----- |
| Deployment package root | `docs/` (this directory) |
| Cloudflare project / working directory | `docs/` |
| After Community export | Exported repo root **is** this package root |
| Install | `npm ci` |
| Build | `npm run build` → VitePress only |
| Proven VitePress output | `.vitepress/dist` |
| Wrangler config | `wrangler.jsonc` (checked in) |
| `assets.directory` | `./.vitepress/dist` |
| Preflight | `npm run deploy:check` |
| CI / Cloudflare upload | `npm run deploy:upload` (or `npm run deploy`) |
| Local convenience (builds once, then uploads) | `npm run deploy:local` |
| Dry-run (no upload) | `npm run deploy:dry-run` |
| Node | `>=22` (matches Wrangler 4.x / Cloudflare static-assets toolchain) |
| Hosting | Cloudflare Workers **Static Assets** |

### Path interpretation rule

All Wrangler paths are relative to the **docs package root**.

| Context | Correct assets directory |
| ------- | ------------------------ |
| Inside `docs/` (Cloudflare root / exported `codestrata-docs`) | `./.vitepress/dist` |
| Monorepo-relative location on disk | `docs/.vitepress/dist` |

**Never** put `docs/.vitepress/dist` in `wrangler.jsonc`. That is the v0.1.0 failure class.

## Build ownership (Approach A)

1. Cloudflare (or CI) runs `npm ci`
2. Cloudflare (or CI) runs `npm run build` **once**
3. Preflight: `npm run deploy:check`
4. Upload existing output: `npm run deploy:upload`

`deploy` / `deploy:upload` must **not** invoke VitePress again.  
`deploy:local` is operator-only convenience and must not be the Cloudflare deploy command.

## Historical failure (v0.1.0)

Sequence observed:

1. `npm clean-install` and `npm run build` succeeded (VitePress OK)
2. `npx wrangler deploy` dynamically installed Wrangler
3. No checked-in config → Wrangler auto-setup in non-interactive CI
4. Inferred `assets.directory = docs/.vitepress/dist`
5. Second build may have run; upload failed because that path did not exist relative to the package working directory

**Conclusion:** Not a VitePress failure — a deployment configuration / working-directory / build-output contract failure.

### Diagnostic steps if “assets.directory does not exist”

1. Confirm Cloudflare / CI working directory is the docs package root
2. Confirm actual VitePress output after build is `.vitepress/dist`
3. Confirm `wrangler.jsonc` lives next to `package.json`
4. Confirm `assets.directory` is `./.vitepress/dist`
5. Run `npm run deploy:check`

## Cloudflare project settings (owner runbook)

Configure the Cloudflare project so:

| Setting | Value |
| ------- | ----- |
| Repository root / project root | `docs` (monorepo subdirectory) **or** the exported `codestrata-docs` repository root |
| Install command | `npm ci` |
| Build command | `npm run build` |
| Build output directory | `.vitepress/dist` |
| Deploy command | `npm run deploy:upload` |
| Wrangler config | `wrangler.jsonc` |
| Node version | 22+ (match `engines.node`) |
| Secrets | Cloudflare environment only — never in git |

Do **not** enable Wrangler interactive setup. Do **not** let CI generate `wrangler.jsonc`.

Production branch / custom domain / DNS remain owner-operated release gates and are **not** claimed by this slice.

## Secrets and security

- No `CLOUDFLARE_API_TOKEN` (or any deploy credential) in source
- Authentication is Cloudflare/environment-managed
- Build requires no product secrets

## Wrangler CLI telemetry

Wrangler may emit its own anonymous CLI telemetry notice. That is **Cloudflare tooling telemetry**, not CodeStrata product telemetry. CodeStrata consent/contracts are unchanged. CI may set `WRANGLER_SEND_METRICS=false` if org policy prefers.

## Preflight contract

`npm run deploy:check` verifies:

- checked-in `wrangler.jsonc`
- local `wrangler` dependency (no `npx` auto-install)
- `assets.directory` === proven `.vitepress/dist`
- output exists with `index.html`, VitePress `assets/`, sitemap, favicon, brand marks
- Community-only publish scope (no Platform/commercial/internal pages)
- deploy scripts do not double-build

## Explicit non-actions (this slice)

- No production `wrangler deploy` during verification
- No Cloudflare project/route/DNS creation from the verifier
- No documentation redesign
- No Design System visual-language change
- No commit / tag / publish / deploy from this slice

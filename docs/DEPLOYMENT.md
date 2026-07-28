# Deployment Readiness — docs.codestrata.ai

**Status:** Prepared, not deployed. Do not configure production DNS from this phase.

## Build output

| Item | Value |
| ---- | ----- |
| Command | `npm run build` |
| Output directory | `docs/.vitepress/dist` |
| Type | Static HTML/CSS/JS + assets |
| Node | `>=20` |

## Environment assumptions

- No backend services
- No CodeStrata Platform runtime
- No secrets required for build
- Optional: `NODE_ENV=production` for production builds

## Custom domain

- Target: `https://docs.codestrata.ai`
- HTTPS required
- DNS ownership: CodeStrata web/ops (future)

## Recommended host

**Recommendation: Cloudflare Pages** (or GitHub Pages as a close alternative).

| Option | Fit |
| ------ | --- |
| **Cloudflare Pages** | Static-native, custom domain, HTTPS, preview deploys, low ops, strong security defaults, cost-efficient |
| GitHub Pages | Simple for public `codestrata-docs`; custom domain supported; preview via Actions artifacts / PR workflows |
| AWS Amplify / S3+CloudFront | Full control; higher ops for equivalent static docs |
| Vercel / Netlify | Excellent DX and previews; evaluate org preference and cost |

**Why Cloudflare Pages first:** static site support, custom domain + HTTPS,
preview environments for Community PRs, low operational overhead, no server
secrets for a docs-only site.

## Preview strategy

- PR builds produce static artifacts or host preview URLs
- Preview hosts must not be confused with the production canonical URL in human copy
- Sitemap hostname remains production-oriented; robots on previews may disallow indexing if the host supports it

## Rollback

- Redeploy previous known-good build artifact / git tag
- Keep prior Cloudflare/GitHub deployment immutable for fast rollback

## Ownership

| Concern | Owner (future) |
| ------- | -------------- |
| Content | Documentation / Community maintainers |
| Deploy pipeline | Docs repo CI |
| DNS / TLS | Web/ops |
| Domain policy | CodeStrata org |

## No-secret default

- No analytics keys in repo by default
- No Platform credentials in CI for docs builds
- Future analytics require privacy review

## Explicit non-actions (this phase)

- No production DNS changes
- No production deploy
- No publishing of `codestrata-docs` remote

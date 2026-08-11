# CodeStrata Documentation

Public **Community Edition** documentation portal for CodeStrata.

- Site root for future deploy: [https://docs.codestrata.ai](https://docs.codestrata.ai)
- Standalone repository name (extraction): **`codestrata-docs`**
- Framework: **VitePress**
- Visual system: consumes [`design-system/`](../design-system/) tokens (Slice 14.1 / 14.2)

Active navigation is Community-only. Historical Platform / commercial pages may
remain on disk for archive but are excluded from publish (`srcExclude`).

Architecture transparency pages:

- [Community Cloud](./architecture/community-cloud)
- [Data Lake](./architecture/data-lake)
- [Insights](./architecture/insights)
- [Source Locality](./security/source-locality)
- [Community Cloud API](./reference/community-api/)

## Local development

Requires **Node.js 22+** (Wrangler 4.x / Cloudflare static-assets toolchain).

```bash
npm ci
npm run dev
```

Other commands:

```bash
npm run build           # VitePress only → .vitepress/dist
npm run preview         # preview production build
npm test                # build + validation
npm run validate        # validation against existing dist
npm run deploy:check    # deployment preflight (no upload)
npm run deploy:dry-run  # local Wrangler dry-run (no upload)
npm run deploy:upload   # production upload via local Wrangler (operator)
```

Cloudflare project root is this `docs/` package. See [DEPLOYMENT.md](./DEPLOYMENT.md).

## Content contribution

- Edit Markdown under section folders (`getting-started/`, `engine/`, …)
- Follow terminology in [ARCHITECTURE.md](./ARCHITECTURE.md) and product model pages
- Run `npm test` before submitting changes
- See [CONTRIBUTING.md](./CONTRIBUTING.md)

## Assets

Place static files in `public/` (copied to site root on build). Theme tokens live in
`.vitepress/theme/tokens.css`.

## Related docs

| Doc | Purpose |
| --- | ------- |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Framework, design tokens, boundaries |
| [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) | Engine docs → portal ownership |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | docs.codestrata.ai readiness |
| [EXTRACTION.md](./EXTRACTION.md) | Standalone repo readiness |
| [CI.md](./CI.md) | CI assumptions |

## License

MIT — see [LICENSE](./LICENSE).

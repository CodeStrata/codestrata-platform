# CodeStrata Documentation

Public documentation portal for **CodeStrata** Community assets.

- Site root for future deploy: [https://docs.codestrata.ai](https://docs.codestrata.ai)
- Standalone repository name (extraction): **`codestrata-docs`**
- Framework: **VitePress** — see [ARCHITECTURE.md](./ARCHITECTURE.md)

## Local development

Requires **Node.js 20+**.

```bash
npm install
npm run dev
```

Other commands:

```bash
npm run build      # production static site → .vitepress/dist
npm run preview    # preview production build
npm test           # build + validation
npm run validate   # validation against existing dist
```

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

# Visual Regression Baseline

Lightweight, unpaid visual validation for the documentation portal.

## Viewports

| Name | Width | Height |
| ---- | ----- | ------ |
| mobile | 390 | 844 |
| tablet | 768 | 1024 |
| laptop | 1280 | 800 |
| wide | 1440 | 900 |

## Pages

- `/` (home) — dark
- `/getting-started/` — dark
- `/reports/` — dark
- `/extensions/vscode` — dark
- `/reference/cli` — dark
- `/` — light (theme toggle)
- `/` — mobile (390)

## Capture command

Requires a running preview server (`npm run preview`, default http://127.0.0.1:4173)
or pass `DOCS_BASE_URL`.

```bash
npm run build
npm run preview -- --host 127.0.0.1 --port 4173 &
npm run visual:capture
```

Baselines are written to:

```text
docs/visual-baselines/
```

## Review process

1. Run capture after visual theme changes.
2. Open PNGs side-by-side with https://codestrata.ai/ screenshots for brand check.
3. Confirm high-impact items in `WEBSITE_STYLE_ALIGNMENT.md` remain **matched**.
4. Do not claim pixel-perfect parity — baselines are a review aid.

## Tooling

Uses Playwright when available (`npx playwright`), otherwise Chromium via
`playwright-core` if installed as a devDependency. The capture script fails with
instructions if no browser runner is present.

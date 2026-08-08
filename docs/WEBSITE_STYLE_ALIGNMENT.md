# Website Style Alignment

Public visual authority for the documentation portal.

## Precedence

1. Live site: https://codestrata.ai/ (inspected 2026-07-28)
2. Published website assets: `https://codestrata.ai/assets/styles.css`, `fonts.css`
3. `design-system/` (`codestrata-visual-design-system:1.0`; brand assets via
   `codestrata-brand-asset-policy:1.0`)
4. Documentation accessibility adaptations (this file)

Website application source is **not** present in this monorepo. Values below were
taken from the live CSS and computed styles (browser CDP), not guessed.

## Website source paths (live)

| Asset | URL |
| ----- | --- |
| Homepage | https://codestrata.ai/ |
| Global CSS | https://codestrata.ai/assets/styles.css |
| Font faces | https://codestrata.ai/assets/fonts.css |
| Fonts | https://codestrata.ai/assets/fonts/*.woff2 |
| Framework | Static HTML + first-party CSS (no React/Vue marketing framework detected in HTML) |

Local brand masters (logos only): `design-system/assets/brand/` — the authority as of
Slice 14.10. Derivatives are generated into `docs/public/brand/` and `docs/public/favicon.svg`
by `scripts/generate_brand_assets.py` so the exported documentation repository is
self-contained. `docs/public/design-tokens/tokens.css` mirrors Design System 1.0
(`design-system/tokens/tokens.css`) as of Slice 14.13 — not the historical live-site
amber capture below. `governance/assets/svg/` is a historical archive and no longer a master.

## Website tokens (captured)

### Dark (default)

| Token | Value |
| ----- | ----- |
| `--bg` | `#0b0d10` |
| `--bg-2` | `#0f1216` |
| `--surface` | `#14171c` |
| `--surface-2` | `#1a1e25` |
| `--border` | `#232830` |
| `--border-2` | `#333a45` |
| `--fg` | `#edeff2` |
| `--fg-muted` | `#9aa3ae` |
| `--fg-dim` | `#6b7480` |
| `--amber` / `--accent` | `#d98a3d` |
| `--amber-bright` | `#eca860` |
| `--amber-deep` | `#b06a24` |
| `--accent-fg` | `#16110a` |
| `--code-bg` | `#0d1014` |
| `--maxw` | `1120px` |
| `--nav-h` | `60px` |
| `--radius` | `10px` |
| `--radius-lg` | `16px` |
| `--radius-xl` | `22px` |
| `--font-display` | Space Grotesk |
| `--font-body` | Inter |
| `--font-mono` | IBM Plex Mono |
| Body size | `17px` / lh 1.6 |
| Header | sticky, `color-mix(bg 80%, transparent)` + blur, border-bottom |

### Light (`[data-theme="light"]`)

| Token | Value |
| ----- | ----- |
| `--bg` | `#ffffff` |
| `--bg-2` / `--surface` | `#f7f8fa` |
| `--surface-2` | `#eef1f4` |
| `--border` | `#e6e8ec` |
| `--fg` | `#0e1116` |
| `--fg-muted` | `#566069` |
| `--accent` | `--amber-deep` (`#b06a24`) |
| `--accent-fg` | `#ffffff` |
| `--code-bg` | `#0f1216` (stays dark) |

## Documentation token mapping

| Website | Docs location |
| ------- | ------------- |
| `:root` tokens | `public/design-tokens/tokens.css` |
| Font faces | `public/fonts.css` + `public/fonts/*.woff2` |
| VitePress bridge | `.vitepress/theme/tokens.css` |
| Buttons / cards / terminal / footer | `.vitepress/theme/components.css` |
| Layout chrome overrides | `.vitepress/theme/custom.css` |
| Footer component | `.vitepress/theme/CsFooter.vue` |
| Logos | `public/brand/*.svg` |

VitePress `--vp-c-*` variables are remapped to CodeStrata tokens so stock indigo /
default greys are not used for brand surfaces.

## Sync process

1. Fetch `https://codestrata.ai/assets/styles.css`
2. Diff `:root` and `[data-theme="light"]` against `public/design-tokens/tokens.css`
3. Update tokens; refresh `WEBSITE_STYLE_ALIGNMENT.md` capture date
4. Rebuild docs (`npm test`)

No runtime dependency on the website repository or `governance/`.

## Intentional differences

| Area | Difference | Reason |
| ---- | ---------- | ------ |
| Navigation items | Docs journeys (Get Started, Engine, …) instead of full marketing nav | Documentation usability |
| Home content | Install / assess / reports CTAs, not “Book an assessment” funnel | Docs purpose |
| Sidebar | VitePress sidebar (styled to brand) | Required for docs IA |
| Search UI | VitePress local search chrome | Docs capability; colors remapped |
| Theme attribute | VitePress `.dark` class bridged to website light/dark tokens | Framework constraint |
| Marketing ambient motion | Scan line / typed cursor not replicated on every docs page | Reduced distraction; `prefers-reduced-motion` respected |
| Consent banner | Not included | Docs collect no analytics by default |

## Accessibility adaptations

| Adaptation | Notes |
| ---------- | ----- |
| `:focus-visible` amber outline | Explicit 2px focus ring on interactive elements |
| `prefers-reduced-motion` | Disables transitions/animations |
| Light theme retained | Brand tokens (not stock VitePress); dark remains primary |
| Code contrast | Dark code surfaces in both themes (matches website) |
| Touch targets | Nav/theme controls ≥34px (website parity) |
| Skip-to-content | VitePress default landmark preserved |

## Side-by-side classification

| Element | Status |
| ------- | ------ |
| Logo lockup | **matched** (Design System brand masters, Slice 14.10) |
| Typography families / weights | **matched** |
| Background / surfaces / borders | **matched** |
| Amber accent | **matched** |
| Container `--maxw` 1120 | **matched** for home/footer; doc prose uses readable measure |
| Header height / blur / border | **matched** (adapted onto VitePress nav shell) |
| Primary / ghost buttons | **matched** |
| Cards | **matched** (docs feature cards + `.cs-card`) |
| Terminal / code | **matched** (`--code-bg`, mono, border, `#d7dde5`) |
| Footer structure / styling | **matched** (docs link groups) |
| Mobile nav drawer | **intentionally adapted** (VitePress hamburger; brand colors) |
| Marketing hero artifact / fog story | **intentionally adapted** (docs hero is documentation-led) |

## Unresolved / residual

| Item | Impact | Notes |
| ---- | ------ | ----- |
| Pixel-identical nav link spacing vs marketing | Low | Docs has more nav items |
| Exact hamburger breakpoint CSS from marketing | Low | VitePress mobile at framework breakpoints |
| Website consent / form components | N/A | Not applicable to docs |
| Automated axe CI gate | Medium follow-up | Manual + screenshot baseline this phase |

No unresolved **high-impact** brand differences remain (background family, fonts,
amber, stock VitePress blue chrome, inconsistent logo/footer/code treatment).

## Visual regression

See `docs/VISUAL_REGRESSION.md`.

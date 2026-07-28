# Platform API Docs — Visual Alignment

**Audience:** Internal engineering  
**Portal:** `/api/docs` (Swagger projection)  
**Authority precedence:**

1. https://codestrata.ai/
2. Community documentation implementation (`docs/`)
3. `docs/WEBSITE_STYLE_ALIGNMENT.md`
4. Shared design tokens (`docs/public/design-tokens/tokens.css`)
5. Accessibility adaptations

## Rule

Do **not** invent a Platform-only theme. Platform API docs must reuse the same
CodeStrata design system as Community documentation.

## Reused surfaces

| Surface | Implementation |
| ------- | -------------- |
| Dark / light / system themes | `swagger/js/theme.js` + `data-theme` |
| Theme persistence | `localStorage` key `codestrata-platform-api-theme` |
| Tokens | Synced copy of Community `tokens.css` |
| Typography | Space Grotesk · Inter · IBM Plex Mono |
| Header / footer | CodeStrata lockups + internal-only nav |
| Cards / borders / focus | Token-driven Swagger overrides |
| Method badges | Semantic HTTP colors retained (intentional) |

## Sync commands

```bash
cp docs/public/design-tokens/tokens.css \
   platform/api/openapi/swagger/design-tokens/tokens.css
cp docs/public/fonts.css platform/api/openapi/swagger/fonts.css
cp docs/public/fonts/*.woff2 platform/api/openapi/swagger/fonts/
python platform/api/openapi/scripts/check_token_drift.py
```

## Intentional differences vs Community docs

| Difference | Why |
| ---------- | --- |
| Swagger operation layout | OpenAPI tooling requires expandable ops; not VitePress pages |
| “Internal” badge + noindex | Access-control / non-public audience |
| Try-it-out disabled by default | Avoid accidental writes against shared environments |
| Footer links only to `/api/*` + probes | No public marketing links |
| CDN Swagger UI bundle | Projection dependency; contract remains local OpenAPI files |

## Validation matrix

| View | Desktop | Mobile | Dark | Light | System |
| ---- | ------- | ------ | ---- | ----- | ------ |
| Shell (header/hero/footer) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Operations list | ✓ | ✓ | ✓ | ✓ | ✓ |
| Schema models | ✓ | ✓ | ✓ | ✓ | ✓ |
| Authorize dialog | ✓ | ✓ | ✓ | ✓ | ✓ |
| Examples / code panels | ✓ | ✓ | ✓ | ✓ | ✓ |

Baselines directory: `baselines/` (structural HTML captures from TestClient).

Capture:

```bash
python platform/api/openapi/scripts/capture_visual_baselines.py
```

## Accessibility

- Skip link to `#swagger-ui`
- Focus rings use `--accent`
- Theme controls expose `aria-pressed`
- `color-scheme` synced with resolved theme

## Non-goals

- Public marketing pages
- Duplicate Community journey content
- Platform-specific purple/glow themes

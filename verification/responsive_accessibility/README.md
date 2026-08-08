# Slice 14.11 — Responsive and accessible experience

Verification package for `codestrata-accessibility-responsive-policy:1.0`.

## Run

```bash
PYTHONPATH=engine/src:platform/src:. python -m verification.responsive_accessibility
```

Optional browser validation uses Playwright Chromium when installed. When the
browser is unavailable, static HTML/CSS/contrast checks remain authoritative and
the report records the limitation.

## Report

`reports/verification/sv14-11/responsive-accessibility-verification.json`

Schema: `responsive-accessibility-verification:1.0.0`

## Boundaries

- Does not change report content, scoring, risk semantics, or report IA
- Does not redesign brand geometry
- Does not modify Wrangler/Cloudflare deployment (Slice 14.12 complete; owned elsewhere)
- Does not claim formal WCAG certification

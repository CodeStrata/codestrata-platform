# Accessibility and responsive experience

**Policy:** `codestrata-accessibility-responsive-policy:1.0` (Slice 14.11)  
**Contracts:** [`design-system/contracts/accessibility.json`](../contracts/accessibility.json), [`design-system/contracts/responsive.json`](../contracts/responsive.json)

## Posture

CodeStrata targets WCAG 2.2 AA-compatible presentation for Community web and
report surfaces. Automated verification is not a substitute for formal
accessibility certification.

Verification distinguishes:

- **PASS** — the surface meets the defined automated/structural accessibility
  contract
- **"WCAG certified"** — must not be claimed unless independently certified

## What this slice owns

- Contrast targets for semantic token combinations (light, dark, print)
- Keyboard access, visible focus, landmarks, skip links, headings
- Table semantics and keyboard-reachable overflow regions
- Image alt contracts and decorative brand-mark hiding
- Reduced motion, forced-colours baseline, dark-theme status/risk inks
- Responsive viewport matrix and page-level overflow prohibition
- Narrow presentation-boundary remediations when defects are found

## What this slice does not own

| Concern | Authority |
| --- | --- |
| Report section order / anchors | Slice 14.9 IA |
| Severity / risk / score semantics | Slice 14.8 visualization |
| Brand mark geometry | Slice 14.10 assets |
| Marketplace gallery strategy | Slice 14.6 |
| Wrangler / Cloudflare deployment | Slice 14.12 |
| VS Code host keyboard / contrast | Native VS Code host |

## Dark-theme status inks

The light brand inks (`--cs-teal`, `--cs-rust`, `--cs-blue`) remain the
authoritative light palette. Slice 14.11 adds dark-surface tints of the same
hues (`--cs-teal-light`, `--cs-rust-light`, `--cs-blue-light`) and remaps
status/risk/score semantics onto those tints inside the dark block only. The
approved light palette is not replaced.

## Surfaces

1. Community Documentation (VitePress)
2. Assessment HTML Report
3. Commercial Engineering Intelligence Report
4. VS Code Community extension (native host; no custom webview)
5. Marketplace visual assets (alt text + fixture contrast)

## Verification

Package: `verification/responsive_accessibility`  
Report: `reports/verification/sv14-11/responsive-accessibility-verification.json`  
Schema: `responsive-accessibility-verification:1.0.0`

## Limitations

- Automated structural and computed checks only — no formal WCAG certification
- Manual screen-reader validation not performed
- Browser validation limited to one Chromium engine on one OS when available
- Print pagination is not publication-quality
- VS Code accessibility is delegated to the native host
- Forced-colours baseline is not validated on Windows High Contrast
- Marketplace screenshots remain raster fixtures

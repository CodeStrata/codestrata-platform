# Slice 14.10 — brand asset verification

Verifies that CodeStrata has exactly one authoritative brand asset system and
that every product surface consumes an approved derivative of it.

## Run

```bash
python -m verification.brand_assets
pytest tests/verification/brand_assets -q
```

Output: `reports/verification/sv14-10/brand-assets-verification.json`
(schema `brand-assets-verification:1.0.0`) plus a short Markdown summary. The
report is deterministic and contains no absolute paths, user data, or clock
values.

## What is verified

- **Policy and contracts** — `codestrata-brand-asset-policy:1.0`,
  `design-system/contracts/assets.json`, `design-system/contracts/icons.json`.
- **Authority** — exactly two masters (mark and wordmark), the Design System owns
  product visuals, the governance package is declared historical, and every
  derivative traces to a master.
- **Master geometry** — the four-bar strata system, its token colours, and the
  contract's mirrored geometry all agree.
- **Variants** — the master set exists, monochrome is `currentColor`, dark
  backgrounds use `night_ink`, and no variant lacks a consumer.
- **SVG safety** — no scripts, event handlers, external references,
  `foreignObject`, live text, font dependencies, editor metadata, or local paths.
  The SVG namespace declaration is excluded from URL scanning.
- **Raster metadata** — packaged rasters carry only `IHDR`/`IDAT`/`IEND` and no
  identity fragments.
- **Duplicates** — every byte-identical pair is either an authorized consumer copy
  or archive content. Third-party validation fixtures are out of scope.
- **Legacy identity** — amber-era hexes are absent from active vectors and from
  the Marketplace raster; AIMF and Cursor have no visual assets.
- **Consumers** — website palette, documentation site, Platform API portal,
  Assessment report, Intelligence report, VS Code, Marketplace, favicon.
- **Icon language** — one custom symbol, generic actions delegated to the host,
  severity semantics delegated to the visualization contract.
- **Export boundary** — consumer copies live inside their own export roots and no
  consumer reaches into `design-system/` at build or runtime.
- **Baselines** — logo contrast on approved backgrounds, decorative versus labelled
  usage, alt-text contract, `viewBox` everywhere, intrinsic scaling.
- **Boundaries** — report information architecture (14.9), visualization semantics
  (14.8), and deployment configuration (14.12) are complete, and Slice 14.13 has
  not started.
- **Determinism** — `scripts/generate_brand_assets.py --check` reports no drift and
  both report renders are stable.

Negative scenarios A–Z cover conflicting masters, revived legacy identities,
derivative-declared-as-master mistakes, unsafe SVG content, raster metadata leaks,
accidental duplicates, colour-only icon meaning, invisible logos, broken export
references, and early Slice 14.13 work.

## Verdict

`PASS_WITH_LIMITATIONS` is expected: independently exported repositories need
self-contained derivative copies, the Marketplace icon stays raster, the VS Code
icon stays a simplified reduction, there is no pixel or browser validation,
and the worktree is uncommitted.

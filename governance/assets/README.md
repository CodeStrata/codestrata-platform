# Governance assets

**Status:** HISTORICAL ARCHIVE (amber-era) — **not** the active Design System authority.

Active Design System 1.0 lives under [`design-system/`](../../design-system/).
Brand masters: [`design-system/assets/brand/`](../../design-system/assets/brand/).
Token authority: [`design-system/tokens/`](../../design-system/tokens/).

This tree retains pre–Design System 1.0 (amber-era) brand rasters, SVGs, and the
legacy `DESIGN-SYSTEM.md` for history. Do not treat files here as product visual
authority. Do not copy amber hex into active consumer surfaces.

## Structure

```text
assets/
├── README.md
├── DESIGN-SYSTEM.md           # historical amber-era notes (non-authoritative)
├── preview.html
├── extension-branding/        # historical marketplace packaging sources
├── favicon/
├── png/
├── svg/
└── social/
```

## Authority

| Asset | Role |
| ----- | ---- |
| [`design-system/`](../../design-system/) | **Authoritative** Design System + brand masters |
| This tree | Historical archive only |
| Packaged Marketplace media | `vscode-plugin/media/` (generated/approved derivatives) |

Product naming (CodeStrata / CodeStrata Engine / CodeStrata Platform) is
documented in [BRANDING_GUIDELINES.md](../standards/BRANDING_GUIDELINES.md).

## Rules

1. Preserve the archive structure; do not delete en masse without owner review.
2. Do not reintroduce amber as an active brand accent.
3. Do not maintain a competing Design System under `standards/`.
4. New brand geometry and colour must come from `design-system/`.

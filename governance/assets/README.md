# Governance assets

**Status:** Uploaded package (canonical)

Brand and Design System assets for CodeStrata live here.

## Structure

```text
assets/
├── README.md
├── DESIGN-SYSTEM.md    # authoritative Design System
├── preview.html
├── favicon/
├── png/
├── svg/
└── social/
```

## Authority

| Asset | Role |
| ----- | ---- |
| [DESIGN-SYSTEM.md](DESIGN-SYSTEM.md) | **Single** Design System source of truth |
| `preview.html` | Local visual review of brand assets |
| `favicon/`, `png/`, `svg/`, `social/` | Uploaded brand package (preserve as provided) |

Product naming (CodeStrata / CodeStrata Engine / CodeStrata Platform) is
documented in [BRANDING_GUIDELINES.md](../standards/BRANDING_GUIDELINES.md).
That document **references** this Design System; it must not duplicate visual
rules.

## Rules

1. Preserve the uploaded package structure.
2. Do not reintroduce placeholder folders (`logos/`, `icons/`, `fonts/`,
   `colors/`, `templates/`, `examples/`).
3. Do not maintain a second copy of the Design System under `standards/`.
4. Future documentation and Product Experience work must cite
   [DESIGN-SYSTEM.md](DESIGN-SYSTEM.md).

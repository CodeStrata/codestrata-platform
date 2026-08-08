# Design System contracts (Slices 14.7–14.13)

Machine-readable **usage** contracts for Design System 1.0.

Primitive/semantic token authority remains:

- `design-system/tokens/catalog.json`
- `design-system/tokens/tokens.css`

These contract files do **not** create a second token source.

| File | Purpose |
| --- | --- |
| `presentation.json` | Typography roles, color/surface roles, spacing/radius/border/shadow, layouts |
| `components.json` | Canonical component semantics across consumers |
| `consumer-mappings.json` | How Docs / Assessment / EIR / VS Code / Marketplace consume the contract |
| `visualization.json` | Semantic visual roles, score/risk/status/confidence mappings, chart grammar (Slice 14.8) |
| `report-information-architecture.json` | Report hierarchy roles, heading/anchor/navigation rules, Assessment and EIR mappings (Slice 14.9) |
| `assets.json` | Brand asset authority, master geometry, approved variants, consumer copies and lineage (Slice 14.10) |
| `icons.json` | Icon-language principles, the single custom symbol, and delegated semantic roles (Slice 14.10) |
| `accessibility.json` | Accessibility acceptance rules, contrast/focus/keyboard/motion baselines (Slice 14.11) |
| `responsive.json` | Breakpoint matrix and responsive layout rules (Slice 14.11) |
| `cross-surface-consistency.json` | Cross-surface consistency matrix, adaptations, and legacy branding rules (Slice 14.13) |

Policies:

- `codestrata-cross-surface-presentation-policy:1.0`
- `codestrata-visualization-policy:1.0`
- `codestrata-report-information-architecture-policy:1.0`
- `codestrata-brand-asset-policy:1.0`
- `codestrata-accessibility-responsive-policy:1.0`
- `codestrata-cross-surface-consistency-policy:1.0`

Design System version remains **1.0** (additive contracts; no version bump).

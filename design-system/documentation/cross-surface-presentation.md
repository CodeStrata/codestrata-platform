# Cross-surface presentation (Slice 14.7)

Policy: `codestrata-cross-surface-presentation-policy:1.0`

## Purpose

After Docs (14.2), Assessment HTML (14.3), EIR (14.4), VS Code (14.5), and
Marketplace visuals (14.6) already look like CodeStrata, Slice 14.7 establishes
the **authoritative cross-surface presentation contract** and removes accidental
visual drift.

This is **not** another redesign.

## Authority

| Concern | Authority |
| --- | --- |
| Tokens | `design-system/tokens/catalog.json` + `tokens.css` |
| Usage contracts | `design-system/contracts/` |
| Policy | `design-system/policies/cross_surface_presentation_policy.json` |

Design System version remains **1.0** (additive contracts; no bump).

## Contracts

- `contracts/presentation.json` — typography roles, colors, surfaces, spacing, radii, borders, shadows, layouts
- `contracts/components.json` — canonical component semantics
- `contracts/consumer-mappings.json` — Docs / Assessment / EIR / VS Code / Marketplace bridges

## Delivery adaptations (not separate systems)

| Mode | Typography delivery |
| --- | --- |
| web_surface | Intended CodeStrata font stacks |
| offline_report | Same stacks; no network fonts |
| native_host | VS Code / system typography |
| raster_asset | Approved local/system-safe fonts |

## Approved exceptions

- Print (white paper / dark ink; token-derived)
- VS Code native host chrome
- Marketplace raster dimensions / system fonts

## Deferred

- Charts / score-risk visualization → **14.8**
- Navigation IA → **14.9**
- Universal assets → **14.10**
- Accessibility acceptance → **14.11** (complete)
- Documentation deployment → **14.12** (not started)

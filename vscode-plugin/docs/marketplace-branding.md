# Marketplace branding (Slice 13.12 + visual assets 14.6)

Policy: `community-vscode-marketplace-branding-policy:1.0`  
Visual assets policy: `codestrata-marketplace-visual-assets-policy:1.0`

## Purpose

Finalize VS Code Marketplace packaging visuals and short-form metadata for
extension **0.2.0**. Runtime assessment behavior is unchanged.

## Visual reference

**Authoritative:** CodeStrata Design System 1.0 (light-first teal).

| Token | Value |
| --- | --- |
| canvas | `#f4f6f3` |
| ink | `#111815` |
| teal | `#16756a` |

Website: [https://codestrata.ai](https://codestrata.ai)

Product name **CodeStrata**. Tagline: *Engineering decisions grounded in code.*

Marketplace gallery assets are maintained under Slice **14.6**
([marketplace-visual-assets.md](./marketplace-visual-assets.md)).

## Product naming

| Field | Value |
| --- | --- |
| Product | CodeStrata |
| Marketplace displayName | CodeStrata – Engineering Intelligence |
| Publisher | `codestrata` |
| Package name | `codestrata-vscode` |
| Version | 0.2.0 |
| Tagline | Engineering decisions grounded in code. |

## Icon

- Packaged: `media/codestrata-icon.png` (128×128 PNG, RGBA)
- Classification: marketplace-specific raster derivative of the master mark (Slice 14.10)
- Activity bar: `media/codestrata-activity.svg` (`currentColor`, Slice 14.5)

## Gallery banner

```json
{ "color": "#f4f6f3", "theme": "light" }
```

Optional art asset: `media/marketplace-banner.png` (1280×640).

## Screenshots

Synthetic fixtures only. Dimensions: **1280×720** (16:9).

| Order | Asset | Role |
| --- | --- | --- |
| 1 | `screenshot-assessment.png` | Assessment workflow |
| 2 | `screenshot-report.png` | Assessment HTML report (Slice 14.3) |
| 3 | `screenshot-progress.png` | Assessment progress / completion |
| 4 | `screenshot-initialization.png` | Repository initialization |
| 5 | `screenshot-ai-assessment.png` | Optional AI assessment |

Safety: no usernames, absolute paths, credentials, proprietary source, non-VS-Code editor branding,
or commercial Platform/EIR/Cloud/Data Lake visuals.

## Claims restrictions

Marketplace short-form copy must not claim automatic CLI install, production
telemetry/Cloud insights, non-VS-Code editor product support, or unqualified
locality overclaims that omit Engine-owned AI provider boundaries.

## Deferred

- Full accessibility epic — complete in Slice **14.11** (`codestrata-accessibility-responsive-policy:1.0`)
- Marketplace publish — human-approved release only

## Related

- [marketplace-visual-assets.md](./marketplace-visual-assets.md)
- [MARKETPLACE.md](../MARKETPLACE.md) (publish runbook; listing copy is README.md)
- [marketplace-documentation.md](./marketplace-documentation.md)
- [PRIVACY.md](../PRIVACY.md) · [source-locality.md](./source-locality.md)

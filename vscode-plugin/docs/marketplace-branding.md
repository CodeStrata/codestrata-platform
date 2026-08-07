# Marketplace branding (Slice 13.12)

Policy: `community-vscode-marketplace-branding-policy:1.0`

## Purpose

Finalize VS Code Marketplace packaging visuals and short-form metadata for
extension **0.2.0**. Runtime assessment behavior is unchanged.

## Visual reference

Current website: [https://codestrata.ai](https://codestrata.ai)

- Dark-first slate background (`#0b0d10` / `#0f1216`)
- Amber accent (`#d98a3d`)
- Product name **CodeStrata**
- Website lede: *Engineering decisions, grounded in code.*

Design tokens mirror: `docs/public/design-tokens/tokens.css`  
Canonical icon masters: `governance/assets/extension-branding/`

Do **not** redesign the website, HTML reports, or the future unified design system here.

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
- Source: `governance/assets/extension-branding/codestrata-extension-icon-128.png`
- High-res master: `codestrata-extension-icon-master-authored.png` (1024)
- Activity bar: `media/codestrata-activity.svg`

## Gallery banner

```json
{ "color": "#0f1216", "theme": "dark" }
```

Optional art asset: `media/marketplace-banner.png` (1280×640; website-aligned).

## Screenshots

Synthetic fixtures only. Preferred dimensions ≈ **1280×720** or **1280×853**.

| Order | Asset | Role |
| --- | --- | --- |
| 1 | `screenshot-findings.png` | Assessment workflow |
| 2 | `screenshot-report.png` | Engineering Intelligence HTML report |
| 3 | `screenshot-progress.png` | Assessment progress |
| 4 | `screenshot-activity.png` | CLI readiness / activity container |
| 5 | `screenshot-recommendations.png` | Recommendations explorer |

Companion (not primary gallery): `screenshot-findings-light.png`.

Safety: no usernames, absolute paths, credentials, proprietary source, or
nonexistent features.

## Claims restrictions

Marketplace short-form copy must not claim automatic CLI install, production
telemetry/Cloud insights, non-VS-Code editor product support, or unqualified
locality overclaims that omit Engine-owned AI provider boundaries.

## Deferred

- ~~Marketplace long-form listing documentation~~ — [marketplace-documentation.md](./marketplace-documentation.md)
- ~~Clean install / update validation~~ — [clean-install-update.md](./clean-install-update.md)
- Broader cross-product visual redesign (future design work)

## Related

- [MARKETPLACE.md](../MARKETPLACE.md) (publish runbook; listing copy is README.md)
- [marketplace-documentation.md](./marketplace-documentation.md)
- [PRIVACY.md](../PRIVACY.md) · [source-locality.md](./source-locality.md)

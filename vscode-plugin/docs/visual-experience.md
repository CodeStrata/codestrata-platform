# VS Code visual experience (Slice 14.5)

Presentation-only alignment of the Community VS Code extension with
CodeStrata Design System **1.0**, while preserving native VS Code UX.

## Principle

```text
CodeStrata identity  +  VS Code native components
```

Do **not** inject website CSS into native editor UI.

## Authority

| Layer | Authority |
| ----- | --------- |
| Runtime behavior | Epic 13 policies (unchanged) |
| Visual language | `codestrata-visual-design-system:1.0` (conceptual mapping) |
| Host chrome colors | VS Code theme |
| This slice policy | `codestrata-vscode-visual-experience-policy:1.0` |

## Design-system → VS Code mapping

| Design System | VS Code expression |
| ------------- | ------------------ |
| Product name / teal identity | Display name, command category, activity icon, output channel |
| Monoline icon language | Activity bar SVG using `currentColor`; ThemeIcons for actions |
| Concise labeling | Progress, notifications, empty states, status tooltips |
| Light/dark tokens | Host theme; no hardcoded notification/menu colors |
| Card/border concepts | Not applicable to native chrome (no custom webview) |

## Native host boundary

Forbidden in TypeScript for native UI styling:

- Importing `design-system/tokens/tokens.css`
- Hardcoded teal/white/black notification backgrounds
- Custom menu/quick-pick colors

Allowed:

- ThemeIcon / ThemeColor APIs
- `currentColor` SVG for activity bar
- Presentation copy strings
- Custom HTML only if a webview already exists (none today)

## Marketplace / asset boundaries

- Marketplace screenshots, gallery banner, and Marketplace icon PNGs: **Slice 14.6**
- Universal logo consolidation: complete in **Slice 14.10**. `media/codestrata-activity.svg`
  is the approved VS Code derivative of the master mark — monochrome `currentColor`,
  simplified three-bar geometry for 16–24px, no brand hex and no wordmark. It is generated
  from the master by `scripts/generate_brand_assets.py`; see
  `design-system/documentation/brand-assets.md`.
- Full accessibility epic: complete in **Slice 14.11** (`codestrata-accessibility-responsive-policy:1.0`)

## Unchanged

- Extension version **0.2.0**
- Assessment schema **1.2**
- Command IDs and configuration keys
- CLI discovery, install guidance-only, assessment, progress semantics, report open, recovery, telemetry consent, source locality

## Verification

`verification/vscode_visual_experience/`  
Schema: `vscode-visual-experience-verification:1.0.0`  
Report: `reports/verification/sv14-5/vscode-visual-experience-verification.json`

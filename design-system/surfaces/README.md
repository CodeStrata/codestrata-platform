# Surface language (define only)

Machine catalog: [`catalog.json`](catalog.json)

Slice 14.1 defines how each product surface **should** look when later slices
apply the system. **No surface is redesigned here.**

## Documentation

Light-first teal/ink on canvas; Space Grotesk headings; Inter body; mono for
commands; bordered paper cards; dark-preferring code blocks; accessible focus.

**Status:** Applied for Community docs in Slice **14.2** (`docs/.vitepress` imports
`design-system/tokens/tokens.css`). Historical amber tokens under
`docs/public/design-tokens/` remain for archive sync only.

## Assessment HTML reports

Evidence-first. Score / evidence / recommendation cards. Mono for paths and IDs.
Teal accents sparingly. No fabricated progress percentages.

**Status:** Applied in Slice **14.3** (`engine` html_v2 embeds design-system tokens).

## Engineering Intelligence reports

Same type stack and chart palette. Panels and tables over decorative dashboards.

**Status:** Applied in Slice **14.4** (Platform static HTML embeds design-system tokens;
HTML template presentation version `eir-static-html-v2`).

## VS Code extension

Follow workbench theme; map semantic colors to teal/rust/blue tokens where
custom webviews exist. Progress stays indeterminate. No marketing card chrome
inside the editor chrome.

**Status:** Applied in Slice **14.5** (native host presentation + `currentColor`
activity SVG). Marketplace gallery assets aligned in Slice **14.6**.

## Marketplace assets

Shipped gallery banner uses Design System `canvas` (`#f4f6f3`) / light theme
(Slice **14.6**). Icon is a marketplace-specific derivative until Slice **14.10**
owns universal logo authority. See
[`vscode-plugin/docs/marketplace-visual-assets.md`](../vscode-plugin/docs/marketplace-visual-assets.md).

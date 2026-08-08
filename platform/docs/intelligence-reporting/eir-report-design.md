# Engineering Intelligence Report design (Slice 14.4)

Presentation-only redesign of the commercial Platform Engineering Intelligence
Report (website-safe static HTML) so it shares the CodeStrata visual language
with codestrata.ai, Community docs (14.2), and Assessment HTML (14.3).

## Authority

| Layer | Authority |
| ----- | --------- |
| Intelligence truth | Platform EIR domain / aggregation (unchanged) |
| Assessment SoT | Engine `report.json` schema **1.2** (unchanged) |
| Visual language | `codestrata-visual-design-system:1.0` |
| Presentation policy | `codestrata-engineering-intelligence-report-design-policy:1.0` |

## Architecture

```text
Engineering Intelligence domain / model
        → existing adapters / website-safe projection
        → WebsiteSafeExportDocument
        → embedded Design System tokens + static HTML CSS
        → deterministic local engineering-intelligence-report.html
```

The renderer formats existing projected values. It must not recalculate
intelligence, invent scores, or invent priorities/timelines.

## Design-system consumption

Tokens are embedded at generation time via `codestrata.design_system.tokens`
into `presentation/static_html/styles.py` (`REPORT_CSS`).

- Self-contained / offline (CSP: `script-src 'none'`, `font-src 'none'`)
- No remote CSS/fonts/scripts
- Brand hex lives in the token artifact

## Brand identity

The product bar renders the same approved report derivative used by the Assessment
report: a monochrome `currentColor` inline SVG mark plus the product name as text.
Asset authority is `codestrata-brand-asset-policy:1.0` (Slice **14.10**). Geometry is
shared with the Assessment mark; only the embedding helper differs, since the EIR
renderer is Platform-owned. The mark is decorative and embedded inline, so the export
stays website-safe with no remote image.

## Presentation contract version

HTML template identity bumped presentation-only:

- previous: `eir-static-html-v1`
- current: `eir-static-html-v2`

Export JSON schema and EIR domain schema remain **1.0**. Assessment schema
remains **1.2**.

## Shell & sections

Stable anchors preserved (`section-scope`, `section-orientation`, …, `main`,
pattern/observation/drilldown IDs). Product bar + cover + sticky TOC +
responsive tables + print-safe layer.

## Explicit non-goals

- Slice **14.5** and later Epic 14 slices
- Comprehensive chart library (14.8 — visualization foundation complete; no invented EIR dashboards)
- Cross-report IA (14.9 — shared structural hierarchy contract only; EIR sections, order, and
  commercial boundary unchanged)
- Brand asset authority (14.10 — the EIR consumes the approved mark derivative)
- VS Code / Marketplace
- Domain calculation / recommendation / AI changes
- Moving EIR ownership into Engine
- Inventing commercial MVP capabilities

## Verification

Package: `verification/engineering_intelligence_report_redesign/`  
Schema: `engineering-intelligence-report-redesign-verification:1.0.0`  
Report: `reports/verification/sv14-4/engineering-intelligence-report-redesign-verification.json`

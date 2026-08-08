# Report navigation / information architecture verification (Slice 14.9)

Schema: `report-navigation-information-architecture-verification:1.0.0`
Policy: `codestrata-report-information-architecture-policy:1.0`
Contract: `design-system/contracts/report-information-architecture.json`

## Purpose

Verify that the Community Assessment HTML report and the commercial Engineering
Intelligence Report share one canonical information hierarchy and navigation
grammar while remaining distinct products.

Both reports are rendered deterministically from synthetic/demonstration
fixtures and inspected structurally — headings, anchors, contents links,
section order, and boundaries.

## Run

```bash
.venv/bin/python -m verification.report_navigation_ia
pytest tests/verification/report_navigation_ia -q
```

Report: `reports/verification/sv14-9/report-navigation-information-architecture-verification.json`

## What is verified

- Canonical hierarchy contract (levels 0–6) with roles and questions
- Single `h1`, no arbitrary heading-level skips in either report
- Unique element ids, kebab-case deterministic section anchors
- Every internal link and contents entry resolves
- Contents entries are presence-driven (no links to absent sections)
- Assessment section order still matches the SV.5 order authority
- EIR section order still matches `SECTION_ORDER`
- Executive orientation precedes technical analysis in both reports
- Findings/evidence/recommendation relationships and placement rules
- Metadata placement, supporting-detail tail, empty/not-assessed states
- Sticky desktop navigation, static mobile contents, print navigation layer
- No JavaScript, no network dependency, no breadcrumbs

## Boundaries

- No schema, scoring, or content-generation changes
- No section reordering
- Visualization semantics owned by Slice 14.8
- Universal assets → 14.10, accessibility acceptance → 14.11 (complete), docs deployment → 14.12 (not started)
- No commit / tag / publish / deploy

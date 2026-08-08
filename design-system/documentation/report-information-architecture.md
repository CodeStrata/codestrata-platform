# Report information architecture (Slice 14.9)

Policy: `codestrata-report-information-architecture-policy:1.0`
Contract: `design-system/contracts/report-information-architecture.json`

## Purpose

One canonical hierarchy and navigation language for CodeStrata reports. The
Community Assessment report and the commercial Engineering Intelligence Report
stay different products with different content; only the structural grammar is
shared.

## Canonical hierarchy

```
0 report identity      Which artifact is this?
1 orientation          What am I looking at?
2 executive summary    What matters?
3 primary analysis     What did CodeStrata evaluate?
4 findings / evidence  What supports these conclusions?
5 recommendations      What should I do next?
6 supporting detail    What reference detail backs the report?
```

A report does not need every level as its own section. The hierarchy defines
semantics, not artificial data parity.

## Headings

`h1` is the report title and appears once. `h2` is a major section, `h3` a
head/capability subsection, `h4` a finding/recommendation/evidence grouping.
Headings are never chosen for visual weight and levels are not skipped.

## Navigation

A single contents navigation per report. Sticky on desktop, static at the top of
the report below 1024px, retained and readable in print. No JavaScript, no
network, no active-scroll tracking, and no breadcrumbs — reports are standalone
artifacts with no parent hierarchy to traverse.

Contents entries are presence-driven: a link is emitted only when the matching
section is rendered.

## Anchors

Section anchors are lowercase, kebab-case, semantic, and deterministic. Entity
anchors derive from canonical IDs. Anchors are preserved or aliased, never
silently dropped — the pre-Epic-3 Domain Intelligence deep links remain as
anchor-only aliases.

## Consumers

| Consumer | Hierarchy scope |
| --- | --- |
| Assessment HTML | cover → leadership/executive band → Assessment Results → Roadmap/AI → Technical Appendix |
| EIR HTML | cover → scope/orientation → capability and head analysis → observations → confidence/limitations/drill-downs → methodology/metadata |

Shared structure does not mean shared scope: EIR sections never appear in the
Community report, and commercial navigation is not documented as Community
functionality.

## Deferred

- Universal assets → **14.10**
- Accessibility acceptance → **14.11** (complete)
- Documentation deployment → **14.12** (not started)

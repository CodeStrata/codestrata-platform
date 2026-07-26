# Report Contract Hardening

Phase 5.12 hardens CodeStrata report JSON/HTML for stable, leadership-ready output
without adding assessment capabilities.

## Envelope

`report.json` remains schema **1.2** with an additive top-level `manifest`:

- report / HTML / contract versions
- CodeStrata version
- repository ID / scan ID
- enabled sections
- generation mode
- explicit `volatile_fields` list for comparisons

Versioned schema file:
`schemas/assessment/codestrata.io/v1.2/AssessmentReport.json`

## Determinism rules

- Findings, recommendations, technologies, and evidence use shared contract sort keys.
- Report-facing finding/recommendation IDs are content-derived UUID5 values
  (`codestrata.reporting.contract.identifiers`); runtime domain UUIDs are remapped at the
  reporting boundary only.
- Duplicate IDs and identical evidence rows are removed.
- Severity / priority / effort / risk / confidence strings are normalized.
- Optional sections are omitted when disabled or empty (roadmap with zero initiatives).
- Repeated-run comparisons use `strip_volatile_fields` / `reports_structurally_equal`.

Volatile paths (ignored for structural equality):

- `assessment.generated_at`
- `assessment.timing`
- `assessment.ai.latency_ms`
- `assessment.static_analysis` (provider durations)
- `manifest.generated_at`

## Validation

```bash
codestrata report validate path/to/report.json [--json]
```

Checks schema version, manifest fields, duplicate IDs, finding references,
evidence links, and roadmap traceability.

## HTML

- Executive Summary first
- Clear section hierarchy and leadership-oriented empty states
- Related finding IDs link to in-page finding anchors
- Machine-readable JSON remains separate from HTML presentation

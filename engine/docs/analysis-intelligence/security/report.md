# Security Report Integration

Phase 4.5.6 — presentation-only Security Intelligence report adapter.

## Contract

`SecurityAssessmentSection` (assessment schema **1.3.0**) is projected by
`SecurityReportAdapter` into `SecurityReportSection` (`report.security` **1.0.0**).

Projection path:

```text
SecurityAssessmentSection
  → SecurityReportAdapter
  → SecurityReportSection
  → report.json assessment.security (optional)
  → HTML #security-assessment
```

## Ownership boundary

The adapter:

- consumes the in-memory assessment section only
- uses deterministic bounded wording
- preserves production / test / unknown distinctions
- preserves assessment and synthesis statuses
- omits sensitive evidence details (fingerprints, previews, raw values)

The adapter does **not**:

- recollect repository-sensitive evidence
- rerun Security rules
- rebuild inventories
- regenerate synthesis
- invent findings, conclusions, recommendations, scores, or compliance claims
- enable upstream analysis gates

## Configuration

```toml
[report.sections.security]
enabled = false
```

Default **false**. Independent of:

- `[evidence.repository_sensitive]`
- `[rules.security]`
- `[assessment.sections.security]`
- `include_synthesis`

Enabling the report gate does not trigger assessment execution. If the report is
enabled but no in-memory Security assessment exists, the section is omitted
(`unavailable` telemetry).

## Status mapping

| Assessment status | Report status |
| ----------------- | ------------- |
| disabled | disabled |
| not_requested | not_requested |
| insufficient_evidence | insufficient_evidence |
| failed | failed |
| partially_succeeded | partially_succeeded |
| succeeded | succeeded |

Synthesis `not_requested` / `disabled` / `failed` → inventory/coverage report
without themes, conclusions, or recommendations. Synthesis `empty` or
`succeeded` → project existing synthesis content when present.

Zero findings are **not** mapped to passed / secure / healthy / low risk.

## JSON

Additive optional key `assessment.security` under existing report schema **1.2**.
Omitted when the report gate is disabled or adaptation fails. Does not duplicate
`security-assessment.json`.

## HTML

Section title **Security Intelligence**, anchor `#security-assessment`, placed
after Dependency Assessment. Rendered only when a report section is present.

## Bounds

| Content | Max |
| ------- | --- |
| Themes | 12 |
| Conclusions | 12 |
| Recommendations | 12 |
| Hotspots | 20 |
| Finding summaries | 20 production + 20 additional |
| Diagnostics | 20 |
| Limitations | 12 |
| Traceability samples | 12 |

## Failure isolation

Adapter failures record a bounded diagnostic/warning, omit or mark the Security
report section failed, and preserve assessment artifacts and other report
sections. No re-analysis fallback.

## Explicit non-claims

This report does not provide:

- comprehensive security scanning
- vulnerability / CVE detection
- runtime security analysis
- secret validity verification
- compliance or pass/fail badges
- scores, grades, or risk indices
- AI-generated narrative

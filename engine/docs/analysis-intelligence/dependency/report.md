# Dependency Report Integration

Phase 4.4.6 — presentation-only CTO report adapter.

## Flow

```
DependencyAssessmentSection (in-memory, schema 1.2.0)
  → DependencyReportAdapter
  → DependencyReportSection (report.dependency @ 1.0.0)
  → report.json assessment.dependency + HTML #dependency-assessment
```

## Gates

```toml
[report.sections.dependency]
enabled = false
```

Independent of evidence/rules/assessment gates. Default **off**.

## Contract

- No manifest parsing, evidence recollection, rule re-evaluation, or synthesis
  reconstruction.
- No reading `dependency-assessment.json` as the primary report source.
- Adapter failures are isolated; other report sections continue.
- Output is deterministic; empty optional groups are omitted in HTML.
- JSON schema for the customer report remains **1.2** (additive key only).

## Executive summary

Deterministic statements derived from assessment conclusions only. Never claims
dependencies are healthy, secure, current, supported, or low-risk.

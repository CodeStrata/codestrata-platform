# Performance Intelligence Report Integration

Phase 4.9.6 — presentation-only report adapter for Performance Assessment 1.2.0.

## Contract

| Item | Value |
| ---- | ----- |
| Report section ID | `report.performance` |
| Report section version | **1.0.0** |
| JSON path | `assessment.performance` in `report.json` |
| HTML anchor | `#performance-assessment` |
| Input | In-memory `PerformanceAssessmentSection` only |
| Gate | `[report.sections.performance] enabled = false` (default) |

## Displayed content

- Overall performance posture
- Executive summary
- Themes / conclusions / recommendations (when synthesis projected)
- Performance family inventory (Signals column)
- Finding inventory summary (Finding IDs + rule/severity/confidence buckets)
- Rule execution summary
- Coverage areas, diagnostics, limitations
- Traceability (Finding IDs + relationship samples)

## Explicit non-scope

- No re-analysis, evidence collection, rule evaluation, or synthesis regeneration
- No AI / LLM execution
- No report-side business logic beyond presentation projection
- No performance / bottleneck / load-suitability scoring

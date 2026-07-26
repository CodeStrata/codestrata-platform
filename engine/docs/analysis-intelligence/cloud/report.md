# Cloud Intelligence Report Integration

Phase 4.7.6 — presentation-only report adapter for Cloud Assessment 1.2.0.

## Contract

| Item | Value |
| ---- | ----- |
| Report section ID | `report.cloud` |
| Report section version | **1.0.0** |
| JSON path | `assessment.cloud` in `report.json` |
| HTML anchor | `#cloud-assessment` |
| Input | In-memory `CloudAssessmentSection` only |
| Gate | `[report.sections.cloud] enabled = false` (default) |

## Displayed content

- Overall cloud posture
- Executive summary
- Themes / conclusions / recommendations (when synthesis projected)
- Technology family inventory
- Finding inventory summary (Finding IDs + rule/severity/confidence buckets)
- Rule execution summary
- Coverage areas, diagnostics, limitations
- Traceability (Finding IDs + relationship samples)

## Explicit non-scope

- No re-analysis, evidence collection, rule evaluation, or synthesis regeneration
- No AI
- No report-side business logic beyond presentation projection
- No readiness / portability / compliance scoring

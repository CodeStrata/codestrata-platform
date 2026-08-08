# Slice 15.3 — Validate Event Schemas & Dashboard Metric Coverage

Data-coverage audit: can existing event contracts support Community Insights metrics?

## Identity

| Field | Value |
| --- | --- |
| Policy | `community-insights-event-coverage-policy:1.0` |
| Schema | `community-insights-event-coverage-verification:1.0.0` |
| Report | `reports/verification/sv15-3/community-insights-event-coverage-verification.json` |

## Run

```bash
PYTHONPATH=engine/src:platform/src:. .venv/bin/python -m verification.community_insights_event_coverage
```

## Boundaries

- No schema activation / ingestion enablement
- No aggregations, APIs, or dashboard UI
- No path redesign
- Slice **15.4** has not started
- No commit / tag / publish / deploy

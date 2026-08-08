# Slice 15.4 — Harden Privacy-Safe Analytics Ingestion

| Field | Value |
| --- | --- |
| Policy | `community-insights-ingestion-policy:1.0` |
| Schema | `community-insights-ingestion-verification:1.0.0` |
| Report | `reports/verification/sv15-4/community-insights-ingestion-verification.json` |
| Activation | `activation_ready_but_production_disabled` |

```bash
PYTHONPATH=engine/src:platform/src:. .venv/bin/python -m verification.community_insights_ingestion
```

No aggregations · No dashboard · Slice 15.7 not started · No commit/tag/publish/deploy

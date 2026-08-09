# Slice 15.11 — Community Insights End-to-End Validation

| Field | Value |
| --- | --- |
| Policy | `community-insights-validation-policy:1.0` |
| Contract | `community-insights-validation-contract:1.0` |
| Schema | `community-insights-validation-verification:1.0.0` |
| Report | `.codestrata-artifacts/validation/suites/sv15-11/community-insights-validation-verification.json` |

Offline/mock validation of the complete Insights path using synthetic Data Lake
fixtures, fake S3, fake secrets, and TestClient HTTPS. No AWS, deploy, or live
ingestion. Slice 15.12 deferred.

```bash
PYTHONPATH=platform/src:. .venv/bin/python -m verification.community_insights_validation
PYTHONPATH=platform/src:. .venv/bin/pytest tests/verification/community_insights_validation -q --tb=line
cd insights && npm test && npm run build
```

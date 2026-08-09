# Slice 15.10 — Community Insights Dashboard

| Field | Value |
| --- | --- |
| Policy | `codestrata-insights-dashboard-policy:1.0` |
| Contract | `codestrata-insights-dashboard-contract:1.0` |
| Schema | `community-insights-dashboard-verification:1.0.0` |
| App | `insights/` |
| Report | `.codestrata-artifacts/validation/suites/sv15-10/community-insights-dashboard-verification.json` |

```bash
cd insights && npm ci && npm test && npm run build
PYTHONPATH=platform/src:. .venv/bin/python -m verification.community_insights_dashboard
PYTHONPATH=platform/src:. .venv/bin/pytest tests/verification/community_insights_dashboard -q --tb=line
```
